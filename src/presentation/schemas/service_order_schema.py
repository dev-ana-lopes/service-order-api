from pydantic import BaseModel, EmailStr, Field, field_validator

from ...domain.validation import (
    is_valid_br_plate,
    is_valid_cpf_cnpj,
    normalize_digits,
    normalize_plate,
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class RegisterResponse(BaseModel):
    user_id: str


class ServiceItemRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., gt=0)


class PartItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=1)


class PartRefRequest(BaseModel):
    part_id: str
    quantity: int = Field(..., ge=1)


class CreateServiceOrderRequest(BaseModel):
    customer_id: str | None = None
    vehicle_id: str | None = None
    customer_name: str | None = Field(default=None, min_length=1, max_length=255)
    customer_cpf_cnpj: str | None = None
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(default=None, min_length=1, max_length=20)
    vehicle_brand: str | None = Field(default=None, min_length=1, max_length=100)
    vehicle_model: str | None = Field(default=None, min_length=1, max_length=100)
    vehicle_year: int | None = Field(default=None, ge=1900, le=2100)
    vehicle_plate: str | None = Field(default=None, min_length=1, max_length=20)
    services: list[ServiceItemRequest] | None = None
    parts: list[PartItemRequest] | None = None
    service_ids: list[str] | None = None
    part_refs: list[PartRefRequest] | None = None

    @field_validator("customer_cpf_cnpj")
    @classmethod
    def validate_cpf_cnpj(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not is_valid_cpf_cnpj(v):
            raise ValueError("Invalid CPF/CNPJ")
        return normalize_digits(v)

    @field_validator("vehicle_plate")
    @classmethod
    def validate_plate(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not is_valid_br_plate(v):
            raise ValueError("Invalid vehicle plate")
        return normalize_plate(v)

    @field_validator("service_ids")
    @classmethod
    def validate_service_ids(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        if len(v) < 1:
            raise ValueError("service_ids must have at least 1 item")
        return v


class CreateServiceOrderResponse(BaseModel):
    service_order_id: str


class ServiceOrderStatusResponse(BaseModel):
    status: str
    approval_decision: str | None = None
    rejection_reason: str | None = None


class ApproveServiceOrderRequest(BaseModel):
    approved: bool
    rejection_reason: str | None = Field(default=None, max_length=500)


class ExternalApprovalDecisionRequest(BaseModel):
    token: str


class ApproveServiceOrderResponse(BaseModel):
    success: bool = True
    status: str
    decision: str
    rejection_reason: str | None = None


class UpdateServiceOrderStatusRequest(BaseModel):
    status: str


class ServiceItemResponse(BaseModel):
    id: str
    description: str
    price: float


class PartItemResponse(BaseModel):
    id: str
    name: str
    price: float
    quantity: int


class ServiceOrderResponse(BaseModel):
    id: str
    customer_id: str
    vehicle_id: str
    status: str
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    budget_total: float
    approval_decision: str | None = None
    approval_decision_at: str | None = None
    rejection_reason: str | None = None
    service_items: list[ServiceItemResponse]
    part_items: list[PartItemResponse]
