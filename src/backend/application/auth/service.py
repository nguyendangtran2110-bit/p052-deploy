import hmac
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.auth.contracts import (
    AuthResult,
    ClientContext,
    ManagementRegistrationCommand,
    ResidentRegistrationCommand,
)
from src.backend.core.config import Settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    NotFoundError,
)
from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole, TokenType
from src.backend.infrastructure.db.base import new_uuid
from src.backend.infrastructure.db.models import ManagementProfile, RefreshSession, Resident, UserAccount
from src.backend.infrastructure.db.repositories import AccountRepository, RefreshSessionRepository
from src.backend.infrastructure.security import (
    JwtTokenService,
    hash_password,
    hash_token,
    verify_and_update_password,
)


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.accounts = AccountRepository(session)
        self.refresh_sessions = RefreshSessionRepository(session)
        self.tokens = JwtTokenService(settings)

    async def register_resident(
        self,
        command: ResidentRegistrationCommand,
        client: ClientContext,
    ) -> AuthResult:
        email = self._normalize_email(command.email)
        resident = await self.session.scalar(
            select(Resident).where(
                Resident.resident_code == command.resident_code.strip(),
                func.lower(Resident.email) == email,
                Resident.is_active.is_(True),
            )
        )
        if resident is None:
            raise AuthorizationError("Resident profile does not match the registration information")
        if await self.accounts.get_by_email(email) or await self.accounts.get_by_resident(resident.id):
            raise ConflictError("An account already exists for this resident or email")

        account = UserAccount(
            email=email,
            password_hash=hash_password(command.password),
            role=ActorRole.RESIDENT.value,
            status=AccountStatus.ACTIVE.value,
            resident_id=resident.id,
            password_changed_at=datetime.now(UTC),
        )
        await self._add_account(account)
        return await self._issue_and_commit(account, client)

    async def bootstrap_management(
        self,
        command: ManagementRegistrationCommand,
        bootstrap_token: str | None,
        client: ClientContext,
    ) -> AuthResult:
        configured_token = self.settings.management_bootstrap_token
        if not configured_token:
            raise ConfigurationError("Management bootstrap is not configured")
        if not bootstrap_token or not hmac.compare_digest(bootstrap_token, configured_token):
            raise AuthenticationError("Bootstrap token is invalid")
        if await self.accounts.count_management() > 0:
            raise ConflictError("The first management administrator has already been created")

        admin_command = ManagementRegistrationCommand(
            email=command.email,
            password=command.password,
            employee_code=command.employee_code,
            full_name=command.full_name,
            management_role=ManagementRole.ADMIN,
            phone=command.phone,
            department=command.department,
            job_title=command.job_title,
            project_code=command.project_code,
            building=command.building,
        )
        account = await self._create_management_account(admin_command)
        return await self._issue_and_commit(account, client)

    async def create_management_account(
        self,
        command: ManagementRegistrationCommand,
        actor: ActorContext,
    ) -> UserAccount:
        if not actor.is_management_admin:
            raise AuthorizationError("Management administrator permission is required")
        account = await self._create_management_account(command)
        await self.session.commit()
        created = await self.accounts.get(account.id)
        if created is None:
            raise NotFoundError("Created management account could not be reloaded")
        return created

    async def login(self, email: str, password: str, client: ClientContext) -> AuthResult:
        account = await self.accounts.get_by_email(self._normalize_email(email))
        valid, updated_hash = verify_and_update_password(password, account.password_hash if account else None)
        now = datetime.now(UTC)

        if account is None or not valid:
            if account is not None:
                account.failed_login_attempts += 1
                if account.failed_login_attempts >= self.settings.auth_max_failed_attempts:
                    account.locked_until = now + timedelta(minutes=self.settings.auth_lockout_minutes)
                    account.failed_login_attempts = 0
                await self.session.commit()
            raise AuthenticationError("Email or password is incorrect")

        if account.locked_until and self._as_utc(account.locked_until) > now:
            raise AuthenticationError("Account is temporarily locked")
        if account.status != AccountStatus.ACTIVE.value:
            raise AuthenticationError("Account is disabled")

        if updated_hash:
            account.password_hash = updated_hash
        account.failed_login_attempts = 0
        account.locked_until = None
        account.last_login_at = now
        return await self._issue_and_commit(account, client)

    async def refresh(self, refresh_token: str, client: ClientContext) -> AuthResult:
        payload = self.tokens.decode(refresh_token, TokenType.REFRESH)
        account_id = self._required_string(payload, "sub")
        session_id = self._required_string(payload, "sid")
        account = await self.accounts.get(account_id)
        refresh_session = await self.refresh_sessions.get_for_update(session_id)
        now = datetime.now(UTC)

        if account is None or refresh_session is None or refresh_session.account_id != account_id:
            raise AuthenticationError("Refresh token is invalid")
        if refresh_session.revoked_at is not None:
            await self._handle_refresh_reuse(account, now)
        if not hmac.compare_digest(refresh_session.token_hash, hash_token(refresh_token)):
            await self._handle_refresh_reuse(account, now)
        if self._as_utc(refresh_session.expires_at) <= now:
            raise AuthenticationError("Refresh token has expired")
        self._validate_account_claims(account, payload)

        refresh_session.revoked_at = now
        result, replacement = await self._build_token_pair(account, client)
        refresh_session.replaced_by_id = replacement.id
        await self.session.commit()
        return result

    async def logout(self, refresh_token: str) -> None:
        payload = self.tokens.decode(refresh_token, TokenType.REFRESH)
        session_id = self._required_string(payload, "sid")
        refresh_session = await self.refresh_sessions.get(session_id)
        if refresh_session and hmac.compare_digest(refresh_session.token_hash, hash_token(refresh_token)):
            if refresh_session.revoked_at is None:
                refresh_session.revoked_at = datetime.now(UTC)
                await self.session.commit()

    async def logout_all(self, actor: ActorContext) -> None:
        if not actor.actor_id:
            raise AuthenticationError("Authentication is required")
        account = await self.accounts.get(actor.actor_id)
        if account is None:
            raise AuthenticationError("Account no longer exists")
        now = datetime.now(UTC)
        account.token_version += 1
        await self.refresh_sessions.revoke_all(account.id, now)
        await self.session.commit()

    async def change_password(self, actor: ActorContext, current_password: str, new_password: str) -> None:
        if not actor.actor_id:
            raise AuthenticationError("Authentication is required")
        account = await self.accounts.get(actor.actor_id)
        if account is None:
            raise AuthenticationError("Account no longer exists")
        valid, _ = verify_and_update_password(current_password, account.password_hash)
        if not valid:
            raise AuthenticationError("Current password is incorrect")
        if hmac.compare_digest(current_password, new_password):
            raise ConflictError("New password must be different from the current password")

        now = datetime.now(UTC)
        account.password_hash = hash_password(new_password)
        account.password_changed_at = now
        account.token_version += 1
        await self.refresh_sessions.revoke_all(account.id, now)
        await self.session.commit()

    async def authenticate_access_token(self, access_token: str) -> ActorContext:
        payload = self.tokens.decode(access_token, TokenType.ACCESS)
        account = await self.accounts.get(self._required_string(payload, "sub"))
        if account is None:
            raise AuthenticationError("Account no longer exists")
        self._validate_account_claims(account, payload)

        role = ActorRole(account.role)
        management_role = self._management_role(account)
        return ActorContext(
            role=role,
            actor_id=account.id,
            resident_id=account.resident_id,
            management_role=management_role,
        )

    async def get_account(self, actor: ActorContext) -> UserAccount:
        if not actor.actor_id:
            raise AuthenticationError("Authentication is required")
        account = await self.accounts.get(actor.actor_id)
        if account is None:
            raise AuthenticationError("Account no longer exists")
        return account

    async def _create_management_account(self, command: ManagementRegistrationCommand) -> UserAccount:
        email = self._normalize_email(command.email)
        if await self.accounts.get_by_email(email):
            raise ConflictError("An account already exists for this email")
        employee_exists = await self.session.scalar(
            select(ManagementProfile.account_id).where(ManagementProfile.employee_code == command.employee_code.strip())
        )
        if employee_exists:
            raise ConflictError("An account already exists for this employee code")

        account = UserAccount(
            email=email,
            password_hash=hash_password(command.password),
            role=ActorRole.MANAGEMENT.value,
            status=AccountStatus.ACTIVE.value,
            password_changed_at=datetime.now(UTC),
        )
        account.management_profile = ManagementProfile(
            employee_code=command.employee_code.strip(),
            full_name=command.full_name.strip(),
            phone=command.phone,
            department=command.department,
            job_title=command.job_title,
            management_role=command.management_role.value,
            project_code=command.project_code,
            building=command.building,
        )
        await self._add_account(account)
        return account

    async def _add_account(self, account: UserAccount) -> None:
        try:
            await self.accounts.add(account)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Account registration conflicts with existing data") from exc

    async def _issue_and_commit(self, account: UserAccount, client: ClientContext) -> AuthResult:
        result, _ = await self._build_token_pair(account, client)
        await self.session.commit()
        loaded_account = await self.accounts.get(account.id)
        if loaded_account is None:
            raise NotFoundError("Authenticated account could not be reloaded")
        return AuthResult(
            account=loaded_account,
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            expires_in=result.expires_in,
        )

    async def _build_token_pair(
        self,
        account: UserAccount,
        client: ClientContext,
    ) -> tuple[AuthResult, RefreshSession]:
        role = ActorRole(account.role)
        management_role = self._management_role(account)
        access = self.tokens.create(
            subject=account.id,
            role=role,
            token_type=TokenType.ACCESS,
            token_version=account.token_version,
            resident_id=account.resident_id,
            management_role=management_role,
        )
        session_id = new_uuid()
        refresh = self.tokens.create(
            subject=account.id,
            role=role,
            token_type=TokenType.REFRESH,
            token_version=account.token_version,
            resident_id=account.resident_id,
            management_role=management_role,
            session_id=session_id,
        )
        refresh_session = RefreshSession(
            id=session_id,
            account_id=account.id,
            token_hash=hash_token(refresh.token),
            expires_at=refresh.expires_at,
            ip_address=client.ip_address,
            user_agent=client.user_agent,
        )
        await self.refresh_sessions.add(refresh_session)
        return (
            AuthResult(
                account=account,
                access_token=access.token,
                refresh_token=refresh.token,
                expires_in=self.settings.jwt_access_token_minutes * 60,
            ),
            refresh_session,
        )

    async def _handle_refresh_reuse(self, account: UserAccount, now: datetime) -> None:
        account.token_version += 1
        await self.refresh_sessions.revoke_all(account.id, now)
        await self.session.commit()
        raise AuthenticationError("Refresh token has been revoked")

    def _validate_account_claims(self, account: UserAccount, payload: dict) -> None:
        if account.status != AccountStatus.ACTIVE.value:
            raise AuthenticationError("Account is disabled")
        if payload.get("role") != account.role or payload.get("ver") != account.token_version:
            raise AuthenticationError("Token has been revoked")
        if account.role == ActorRole.RESIDENT.value and payload.get("resident_id") != account.resident_id:
            raise AuthenticationError("Token identity is invalid")
        management_role = self._management_role(account)
        if management_role and payload.get("management_role") != management_role.value:
            raise AuthenticationError("Token permissions are stale")

    @staticmethod
    def _management_role(account: UserAccount) -> ManagementRole | None:
        if account.role != ActorRole.MANAGEMENT.value:
            return None
        if account.management_profile is None:
            raise AuthenticationError("Management profile is missing")
        return ManagementRole(account.management_profile.management_role)

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _required_string(payload: dict, claim: str) -> str:
        value = payload.get(claim)
        if not isinstance(value, str) or not value:
            raise AuthenticationError(f"Token claim '{claim}' is invalid")
        return value

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
