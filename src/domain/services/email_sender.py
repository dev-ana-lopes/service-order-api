from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalRequestEmailMessage:
    customer_email: str
    service_order_id: str
    total: float
    summary_lines: tuple[str, ...]
    approve_token: str
    reject_token: str


class EmailSender(ABC):
    @abstractmethod
    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        pass

    @abstractmethod
    async def send_status_changed(
        self, customer_email: str, service_order_id: str, new_status: str
    ) -> None:
        pass

    @abstractmethod
    async def send_approval_request(
        self,
        message: ApprovalRequestEmailMessage,
    ) -> None:
        pass
