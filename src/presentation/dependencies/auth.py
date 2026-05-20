from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from ...application.auth.use_cases import PrincipalResolver
from ...domain.contracts.token_verifier import AuthenticatedPrincipal
from ...domain.services import AccessTokenService
from ...infrastructure.auth.jwt_token_verifier import JwtTokenVerifier
from .db_dependencies import get_jwt_service
from ...infrastructure.config.settings import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_customer_token_verifier(
    settings: Settings = Depends(get_settings),
) -> JwtTokenVerifier:
    return JwtTokenVerifier(settings)


def get_principal_resolver(
    admin_token_service: AccessTokenService = Depends(get_jwt_service),
    customer_token_verifier: JwtTokenVerifier = Depends(get_customer_token_verifier),
) -> PrincipalResolver:
    return PrincipalResolver(
        admin_token_service=admin_token_service,
        customer_token_verifier=customer_token_verifier,
    )


async def get_current_principal(
    request: Request,
    token: str = Depends(oauth2_scheme),
    resolver: PrincipalResolver = Depends(get_principal_resolver),
) -> AuthenticatedPrincipal:
    principal = resolver.execute(token)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.principal = principal
    return principal


async def require_admin_principal(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthenticatedPrincipal:
    if not principal.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return principal


async def require_customer_or_admin_principal(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> AuthenticatedPrincipal:
    if principal.role not in {"admin", "customer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsupported principal role",
        )
    return principal
