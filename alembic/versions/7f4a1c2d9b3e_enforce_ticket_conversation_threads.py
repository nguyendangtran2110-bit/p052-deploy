"""enforce one conversation per ticket

Revision ID: 7f4a1c2d9b3e
Revises: 64db9979d1f4
Create Date: 2026-08-10 10:00:00.000000
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "7f4a1c2d9b3e"
down_revision: str | Sequence[str] | None = "64db9979d1f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(UTC)
    tickets = sa.table(
        "tickets",
        sa.column("id", sa.String(36)),
        sa.column("resident_id", sa.String(36)),
        sa.column("unit_id", sa.String(36)),
        sa.column("conversation_id", sa.String(36)),
    )
    conversations = sa.table(
        "conversations",
        sa.column("id", sa.String(36)),
        sa.column("resident_id", sa.String(36)),
        sa.column("unit_id", sa.String(36)),
        sa.column("status", sa.String(20)),
        sa.column("last_message_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    messages = sa.table(
        "messages",
        sa.column("id", sa.String(36)),
        sa.column("conversation_id", sa.String(36)),
        sa.column("role", sa.String(20)),
        sa.column("content", sa.Text()),
        sa.column("intent", sa.String(100)),
        sa.column("citations", sa.JSON()),
        sa.column("action_payload", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    seen_conversations: set[str] = set()
    rows = connection.execute(
        sa.select(
            tickets.c.id,
            tickets.c.resident_id,
            tickets.c.unit_id,
            tickets.c.conversation_id,
        ).order_by(tickets.c.id)
    ).mappings()
    for row in rows:
        conversation_id = row["conversation_id"]
        if conversation_id and conversation_id not in seen_conversations:
            seen_conversations.add(conversation_id)
            continue

        new_conversation_id = str(uuid4())
        connection.execute(
            sa.insert(conversations).values(
                id=new_conversation_id,
                resident_id=row["resident_id"],
                unit_id=row["unit_id"],
                status="active",
                last_message_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        connection.execute(
            sa.update(tickets)
            .where(tickets.c.id == row["id"])
            .values(conversation_id=new_conversation_id)
        )
        connection.execute(
            sa.insert(messages).values(
                id=str(uuid4()),
                conversation_id=new_conversation_id,
                role="system",
                content="Ticket conversation initialized during database migration.",
                intent="ticket_conversation_migrated",
                citations=[],
                action_payload={"ticket_id": row["id"]},
                created_at=now,
            )
        )
        seen_conversations.add(new_conversation_id)

    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column(
            "conversation_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        batch_op.drop_index(op.f("ix_tickets_conversation_id"))
    op.create_index("uq_ticket_conversation_id", "tickets", ["conversation_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_ticket_conversation_id", table_name="tickets")
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column(
            "conversation_id",
            existing_type=sa.String(length=36),
            nullable=True,
        )
        batch_op.create_index(op.f("ix_tickets_conversation_id"), ["conversation_id"], unique=False)
