from pydantic import BaseModel, Field

from src.backend.schemas.auth import AccountResponse
from src.backend.schemas.residents import ResidentResponse, ResidentUnitSummary


class ManagementAccountListResponse(BaseModel):
    items: list[AccountResponse]
    total: int
    offset: int
    limit: int


class ManagementResidentResponse(ResidentResponse):
    account: AccountResponse | None = None
    units: list[ResidentUnitSummary] = Field(default_factory=list)


class ManagementResidentListResponse(BaseModel):
    items: list[ManagementResidentResponse]
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
