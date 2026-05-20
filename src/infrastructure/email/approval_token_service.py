from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import ExpiredSignatureError, JWTError, jwt

from ...domain.errors import ExpiredApprovalTokenError, InvalidApprovalTokenError
from ...domain.services import ApprovalTokenPayload, ApprovalTokenService
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class JwtApprovalTokenService(ApprovalTokenService):
    PURPOSE = "service_order_approval"

    def __init__(self, settings: Settings):
        self.settings = settings

    def generate_token(self, service_order_id: UUID, approved: bool) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.APPROVAL_TOKEN_TTL_MINUTES
        )
        payload = {
            "sub": str(service_order_id),
            "decision": "approve" if approved else "reject",
            "purpose": self.PURPOSE,
            "exp": expires_at,
        }
        token = jwt.encode(
            payload,
            self.settings.approval_token_secret,
            algorithm=self.settings.JWT_ALGORITHM,
        )
        logger.info(
            "Generated approval token for service order %s with decision=%s exp=%s",
            service_order_id,
            payload["decision"],
            expires_at.isoformat(),
        )
        return token

    def verify_token(self, token: str) -> ApprovalTokenPayload:
        try:
            payload = jwt.decode(
                token,
                self.settings.approval_token_secret,
                algorithms=[self.settings.JWT_ALGORITHM],
            )
        except ExpiredSignatureError as exc:
            logger.warning("Expired approval token received")
            raise ExpiredApprovalTokenError("Approval token has expired") from exc
        except JWTError as exc:
            logger.warning("Invalid approval token received")
            raise InvalidApprovalTokenError("Approval token is invalid") from exc

        if payload.get("purpose") != self.PURPOSE:
            logger.warning("Approval token rejected due to invalid purpose")
            raise InvalidApprovalTokenError("Approval token is invalid")

        raw_service_order_id = payload.get("sub")
        decision = payload.get("decision")
        raw_exp = payload.get("exp")
        if not raw_service_order_id or decision not in {"approve", "reject"}:
            logger.warning("Approval token rejected due to malformed payload")
            raise InvalidApprovalTokenError("Approval token is invalid")

        expires_at = self._parse_expiration(raw_exp)
        try:
            service_order_id = UUID(raw_service_order_id)
        except ValueError as exc:
            logger.warning("Approval token rejected due to malformed UUID")
            raise InvalidApprovalTokenError("Approval token is invalid") from exc

        return ApprovalTokenPayload(
            service_order_id=service_order_id,
            approved=decision == "approve",
            expires_at=expires_at,
        )

    def _parse_expiration(self, raw_exp: object) -> datetime:
        if isinstance(raw_exp, (int, float)):
            return datetime.fromtimestamp(raw_exp, tz=timezone.utc)
        raise InvalidApprovalTokenError("Approval token is invalid")
