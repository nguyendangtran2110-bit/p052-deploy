from pydantic import BaseModel

from src.backend.domain.onboarding.enums import OnboardingItemStatus


class OnboardingItemStatusRequest(BaseModel):
    status: OnboardingItemStatus
