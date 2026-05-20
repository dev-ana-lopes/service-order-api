from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ApprovalTokenPayload:
    service_order_id: UUID
    approved: bool
    expires_at: datetime


class ApprovalTokenService(ABC):
    @abstractmethod
    def generate_token(self, service_order_id: UUID, approved: bool) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> ApprovalTokenPayload:
        pass
