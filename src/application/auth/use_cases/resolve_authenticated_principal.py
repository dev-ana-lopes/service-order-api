from __future__ import annotations

from dataclasses import dataclass

from ....domain.contracts.token_verifier import AuthenticatedPrincipal, TokenVerifier
from ....domain.services import AccessTokenService


@dataclass
class PrincipalResolver:
    admin_token_service: AccessTokenService
    customer_token_verifier: TokenVerifier

    def execute(self, token: str) -> AuthenticatedPrincipal | None:
        customer_principal = self.customer_token_verifier.verify(token)
        if customer_principal is not None:
            return customer_principal

        admin_payload = self.admin_token_service.verify_token(token)
        if admin_payload is None:
            return None

        return AuthenticatedPrincipal(
            subject=str(admin_payload.get("user_id", "")),
            role="admin",
            customer_id=None,
            issuer=admin_payload.get("iss"),
            claims=admin_payload,
        )
