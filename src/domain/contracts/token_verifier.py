from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    role: str
    customer_id: str | None
    issuer: str | None
    claims: dict[str, Any]

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_customer(self) -> bool:
        return self.role == "customer"


class TokenVerifier(ABC):
    @abstractmethod
    def verify(self, token: str) -> AuthenticatedPrincipal | None:
        raise NotImplementedError
