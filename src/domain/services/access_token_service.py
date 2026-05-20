from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AccessTokenService(ABC):
    @abstractmethod
    def create_token(self, user_id: str, email: str) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> dict[str, Any] | None:
        pass
