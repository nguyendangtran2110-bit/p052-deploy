from pydantic import BaseModel

from src.backend.schemas.auth import AccountResponse


class ManagementAccountListResponse(BaseModel):
    items: list[AccountResponse]
    total: int
    offset: int
    limit: int


class ManagementDashboardResponse(BaseModel):
    ticket_total: int
    ticket_status_counts: dict[str, int]
    ticket_priority_counts: dict[str, int]
    unassigned_tickets: int
    overdue_tickets: int
    active_residents: int
    active_units: int
    active_management_accounts: int
    knowledge_documents_requiring_attention: int
