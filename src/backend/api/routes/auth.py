from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_authenticated
from src.backend.application.auth.contracts import (
    AuthResult,
    ClientContext,
    ManagementRegistrationCommand,
    PasswordResetRequestResult,
    ResidentRegistrationCommand,
)
from src.backend.application.auth.service import AuthService
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.infrastructure.email import EmailService
from src.backend.schemas.auth import (
    AccountResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ManagementBootstrapRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    ResidentRegistrationRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register/resident", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_resident(
    payload: ResidentRegistrationRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    result = await AuthService(session, settings).register_resident(
        ResidentRegistrationCommand(
            resident_code=payload.resident_code,
            email=str(payload.email),
            password=payload.password,
        ),
        _client_context(request),
    )
    return _token_response(result)


@router.post("/bootstrap-management", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_management(
    payload: ManagementBootstrapRequest,
    request: Request,
    bootstrap_token: Annotated[str | None, Header(alias="X-Bootstrap-Token")] = None,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    result = await AuthService(session, settings).bootstrap_management(
        ManagementRegistrationCommand(
            email=str(payload.email),
            password=payload.password,
            employee_code=payload.employee_code,
            full_name=payload.full_name,
            phone=payload.phone,
            department=payload.department,
            job_title=payload.job_title,
            project_code=payload.project_code,
            building=payload.building,
        ),
        bootstrap_token,
        _client_context(request),
    )
    return _token_response(result)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    result = await AuthService(session, settings).login(str(payload.email), payload.password, _client_context(request))
    return _token_response(result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    result = await AuthService(session, settings).refresh(payload.refresh_token, _client_context(request))
    return _token_response(result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    await AuthService(session, settings).logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    actor: ActorContext = Depends(require_authenticated),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    await AuthService(session, settings).logout_all(actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    actor: ActorContext = Depends(require_authenticated),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    await AuthService(session, settings).change_password(actor, payload.current_password, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    result = await AuthService(session, settings).request_password_reset(str(payload.email))
    if isinstance(result, PasswordResetRequestResult):
        background_tasks.add_task(
            EmailService(settings).send_password_reset_email,
            result.email,
            result.raw_token,
        )
    return {"message": "If an active account matches this email, a password reset link will be sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    await AuthService(session, settings).reset_password(payload.token, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AccountResponse)
async def get_me(
    actor: ActorContext = Depends(require_authenticated),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AccountResponse:
    account = await AuthService(session, settings).get_account(actor)
    return AccountResponse.model_validate(account)


def _client_context(request: Request) -> ClientContext:
    return ClientContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
    )


def _token_response(result: AuthResult) -> TokenResponse:
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        account=AccountResponse.model_validate(result.account),
    )
