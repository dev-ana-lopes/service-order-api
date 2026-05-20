from pydantic import BaseModel, EmailStr, Field, field_validator

from ...domain.validation import (
    is_valid_br_plate,
    is_valid_cpf_cnpj,
    normalize_digits,
    normalize_plate,
)


class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    cpf_cnpj: str | None = None
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    is_active: bool = True

    @field_validator("cpf_cnpj")
    @classmethod
    def validate_cpf_cnpj(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not is_valid_cpf_cnpj(v):
            raise ValueError("Invalid CPF/CNPJ")
        return normalize_digits(v)


class CustomerUpdateRequest(CustomerCreateRequest):
    pass


class CustomerResponse(BaseModel):
    id: str
    name: str
    cpf_cnpj: str | None
    email: EmailStr
    phone: str
    is_active: bool


class VehicleCreateRequest(BaseModel):
    customer_id: str
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1900, le=2100)
    plate: str = Field(..., min_length=1, max_length=20)

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        if not is_valid_br_plate(v):
            raise ValueError("Invalid vehicle plate")
        return normalize_plate(v)


class VehicleUpdateRequest(VehicleCreateRequest):
    pass


class VehicleResponse(BaseModel):
    id: str
    customer_id: str
    brand: str
    model: str
    year: int
    plate: str


class CatalogServiceCreateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., gt=0)


class CatalogServiceUpdateRequest(CatalogServiceCreateRequest):
    pass


class CatalogServiceResponse(BaseModel):
    id: str
    description: str
    price: float


class InventoryPartCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    unit_price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)


class InventoryPartUpdateRequest(InventoryPartCreateRequest):
    pass


class InventoryPartResponse(BaseModel):
    id: str
    name: str
    unit_price: float
    stock_quantity: int


class AverageExecutionTimeResponse(BaseModel):
    average_execution_time_seconds: float | None
