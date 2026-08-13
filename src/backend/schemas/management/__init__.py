from src.backend.schemas.management.requests import (
    ManagementAccountCreateRequest,
    ManagementAccountUpdateRequest,
    ManagementResidentUpdateRequest,
    TicketAssignmentRequest,
)
from src.backend.schemas.management.responses import (
    ManagementAccountListResponse,
    ManagementDashboardResponse,
    ManagementResidentListResponse,
    ManagementResidentResponse,
)

__all__ = [
    "ManagementAccountCreateRequest",
    "ManagementAccountListResponse",
    "ManagementAccountUpdateRequest",
    "ManagementResidentListResponse",
    "ManagementResidentResponse",
    "ManagementResidentUpdateRequest",
    "ManagementDashboardResponse",
    "TicketAssignmentRequest",
]
