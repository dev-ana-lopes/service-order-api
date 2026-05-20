from __future__ import annotations

from jose import JWTError, jwt

from ...domain.contracts.token_verifier import AuthenticatedPrincipal, TokenVerifier
from ..config.settings import Settings


class JwtTokenVerifier(TokenVerifier):
    def __init__(self, settings: Settings):
        self.settings = settings

    def verify(self, token: str) -> AuthenticatedPrincipal | None:
        if not self.settings.CUSTOMER_JWT_SECRET:
            return None

        try:
            payload = jwt.decode(
                token,
                self.settings.CUSTOMER_JWT_SECRET,
                algorithms=[self.settings.CUSTOMER_JWT_ALGORITHM],
                issuer=self.settings.CUSTOMER_JWT_ISSUER,
                options={"verify_aud": False},
            )
        except JWTError:
            return None

        if payload.get("role") != "customer":
            return None

        customer_id = payload.get("customer_id")
        subject = payload.get("sub")
        if not customer_id or not subject:
            return None

        return AuthenticatedPrincipal(
            subject=str(subject),
            role="customer",
            customer_id=str(customer_id),
            issuer=payload.get("iss"),
            claims=payload,
        )
