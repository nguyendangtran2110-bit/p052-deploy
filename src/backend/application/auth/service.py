import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.application.auth.contracts import (
    AuthResult,
    ClientContext,
    EmailVerificationRequestResult,
    ManagementRegistrationCommand,
    PasswordResetRequestResult,
    ResidentRegistrationCommand,
)
from src.backend.application.onboarding.service import OnboardingService
from src.backend.core.config import Settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    InvalidVerificationCodeError,
    NotFoundError,
    RateLimitError,
)
from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole, TokenType
from src.backend.infrastructure.db.base import new_uuid
from src.backend.infrastructure.db.models import (
    EmailVerificationToken,
    ManagementProfile,
    PasswordResetToken,
    RefreshSession,
    Resident,
    UserAccount,
)
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

    async def request_resident_registration(
        self,
        command: ResidentRegistrationCommand,
        client: ClientContext,
    ) -> EmailVerificationRequestResult | None:
        email = self._normalize_email(command.email)
        resident_code = command.resident_code.strip()
        resident = await self.session.scalar(
            select(Resident).where(
                Resident.resident_code == resident_code,
                func.lower(Resident.email) == email,
                Resident.is_active.is_(True),
            )
        )
        if resident is None:
            return None
        if await self.accounts.get_by_email(email) or await self.accounts.get_by_resident(resident.id):
            return None

        now = datetime.now(UTC)
        await self._enforce_verification_send_limits(email, now, client.ip_address)
        await self._invalidate_active_email_verifications(email, now)
        raw_code = self._new_verification_code()
        self.session.add(
            EmailVerificationToken(
                email=email,
                request_ip=client.ip_address,
                resident_id=resident.id,
                resident_code=resident_code,
                password_hash=hash_password(command.password),
                token_hash=hash_token(raw_code),
                expires_at=now + timedelta(minutes=self.settings.email_verification_token_minutes),
            )
        )
        await self.session.commit()
        return EmailVerificationRequestResult(email=email, raw_code=raw_code)

    async def resend_resident_registration_code(
        self, email: str, client: ClientContext
    ) -> EmailVerificationRequestResult | None:
        normalized_email = self._normalize_email(email)
        token = await self.session.scalar(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.email == normalized_email, EmailVerificationToken.used_at.is_(None))
            .order_by(desc(EmailVerificationToken.created_at))
            .limit(1)
        )
        if token is None:
            return None

        resident = await self.session.get(Resident, token.resident_id)
        if (
            resident is None
            or not resident.is_active
            or resident.email is None
            or self._normalize_email(resident.email) != normalized_email
            or await self.accounts.get_by_email(normalized_email)
        ):
            return None

        now = datetime.now(UTC)
        await self._enforce_verification_send_limits(normalized_email, now, client.ip_address)
        await self._invalidate_active_email_verifications(normalized_email, now)
        raw_code = self._new_verification_code()
        self.session.add(
            EmailVerificationToken(
                email=normalized_email,
                request_ip=client.ip_address,
                resident_id=token.resident_id,
                resident_code=token.resident_code,
                password_hash=token.password_hash,
                token_hash=hash_token(raw_code),
                expires_at=now + timedelta(minutes=self.settings.email_verification_token_minutes),
            )
        )
        await self.session.commit()
        return EmailVerificationRequestResult(email=normalized_email, raw_code=raw_code)

    async def verify_resident_email(self, email: str, code: str, client: ClientContext) -> AuthResult:
        normalized_email = self._normalize_email(email)
        token = await self.session.scalar(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.email == normalized_email, EmailVerificationToken.used_at.is_(None))
            .order_by(desc(EmailVerificationToken.created_at))
            .limit(1)
            .with_for_update()
        )
        if token is None:
            raise InvalidVerificationCodeError("Verification code is invalid or expired")

        now = datetime.now(UTC)
        if self._as_utc(token.expires_at) <= now:
            token.used_at = now
            await self.session.commit()
            raise InvalidVerificationCodeError("Verification code is invalid or expired")
        if token.attempt_count >= self.settings.email_verification_max_attempts:
            raise RateLimitError("Too many verification attempts")

        if not hmac.compare_digest(token.token_hash, hash_token(code)):
            token.attempt_count += 1
            exhausted = token.attempt_count >= self.settings.email_verification_max_attempts
            if exhausted:
                token.used_at = now
            await self.session.commit()
            if exhausted:
                raise RateLimitError("Too many verification attempts")
            raise InvalidVerificationCodeError("Verification code is invalid or expired")

        resident = await self.session.get(Resident, token.resident_id)
        if (
            resident is None
            or not resident.is_active
            or resident.email is None
            or self._normalize_email(resident.email) != normalized_email
            or resident.resident_code != token.resident_code
        ):
            token.used_at = now
            await self.session.commit()
            raise InvalidVerificationCodeError("Verification code is invalid or expired")
        if await self.accounts.get_by_email(normalized_email) or await self.accounts.get_by_resident(resident.id):
            token.used_at = now
            await self.session.commit()
            raise ConflictError("An account already exists for this resident or email")

        token.used_at = now
        account = UserAccount(
            email=normalized_email,
            password_hash=token.password_hash,
            role=ActorRole.RESIDENT.value,
            status=AccountStatus.ACTIVE.value,
            resident_id=resident.id,
            password_changed_at=now,
            email_verified_at=now,
        )
        await self._add_account(account)
        await OnboardingService(self.session).ensure_for_resident(resident.id)
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
        if account.role == ActorRole.RESIDENT.value and account.email_verified_at is None:
            raise AuthenticationError("Email verification is required")

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

    async def request_password_reset(self, email: str) -> PasswordResetRequestResult | None:
        account = await self.accounts.get_by_email(self._normalize_email(email))
        if account is None or account.status != AccountStatus.ACTIVE.value:
            return None

        now = datetime.now(UTC)
        await self.session.execute(
            PasswordResetToken.__table__.update()
            .where(
                PasswordResetToken.account_id == account.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        raw_token = secrets.token_urlsafe(32)
        self.session.add(
            PasswordResetToken(
                account_id=account.id,
                token_hash=hash_token(raw_token),
                expires_at=now + timedelta(minutes=self.settings.password_reset_token_minutes),
            )
        )
        await self.session.commit()
        return PasswordResetRequestResult(email=account.email, raw_token=raw_token)

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        now = datetime.now(UTC)
        token = await self.session.scalar(
            select(PasswordResetToken)
            .options(selectinload(PasswordResetToken.account).selectinload(UserAccount.management_profile))
            .where(
                PasswordResetToken.token_hash == hash_token(raw_token),
                PasswordResetToken.used_at.is_(None),
            )
            .with_for_update()
        )
        if token is None or self._as_utc(token.expires_at) <= now:
            raise AuthenticationError("Password reset token is invalid or expired")
        account = token.account
        if account.status != AccountStatus.ACTIVE.value:
            raise AuthenticationError("Account is disabled")

        token.used_at = now
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

        now = datetime.now(UTC)
        account = UserAccount(
            email=email,
            password_hash=hash_password(command.password),
            role=ActorRole.MANAGEMENT.value,
            status=AccountStatus.ACTIVE.value,
            password_changed_at=now,
            email_verified_at=now,
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

    async def _enforce_verification_send_limits(
        self, email: str, now: datetime, request_ip: str | None
    ) -> None:
        window_start = now - timedelta(minutes=self.settings.email_verification_window_minutes)
        recent = list(
            (
                await self.session.scalars(
                    select(EmailVerificationToken)
                    .where(
                        EmailVerificationToken.email == email,
                        EmailVerificationToken.created_at >= window_start,
                    )
                    .order_by(desc(EmailVerificationToken.created_at))
                )
            ).all()
        )
        if recent:
            latest_created_at = self._as_utc(recent[0].created_at)
            if (now - latest_created_at).total_seconds() < self.settings.email_verification_resend_cooldown_seconds:
                raise RateLimitError("Please wait before requesting another verification code")
        if len(recent) >= self.settings.email_verification_max_sends:
            raise RateLimitError("Too many verification codes requested")
        if request_ip:
            recent_ip_count = await self.session.scalar(
                select(func.count(EmailVerificationToken.id)).where(
                    EmailVerificationToken.request_ip == request_ip,
                    EmailVerificationToken.created_at >= window_start,
                )
            )
            if int(recent_ip_count or 0) >= self.settings.email_verification_max_ip_sends:
                raise RateLimitError("Too many verification codes requested from this network")

    async def _invalidate_active_email_verifications(self, email: str, now: datetime) -> None:
        await self.session.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.email == email, EmailVerificationToken.used_at.is_(None))
            .values(used_at=now)
        )

    @staticmethod
    def _new_verification_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def _required_string(payload: dict, claim: str) -> str:
        value = payload.get(claim)
        if not isinstance(value, str) or not value:
            raise AuthenticationError(f"Token claim '{claim}' is invalid")
        return value

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
