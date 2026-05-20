from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ....application.use_cases.customer_use_cases import (
    CreateCustomerUseCase,
    DeleteCustomerUseCase,
    GetCustomerUseCase,
    ListCustomersUseCase,
    UpdateCustomerUseCase,
)
from ....domain.contracts.token_verifier import AuthenticatedPrincipal
from ....domain.repositories import CustomerRepository
from ....presentation.dependencies.auth import require_admin_principal
from ....presentation.dependencies.db_dependencies import get_customer_repository
from ....presentation.schemas.admin_schema import (
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)

CustomerRepo = Annotated[CustomerRepository, Depends(get_customer_repository)]
AdminPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_admin_principal)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CustomerCreateRequest,
    customer_repo: CustomerRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = CreateCustomerUseCase(customer_repo)
    try:
        customer_id = await use_case.execute(
            request.name,
            request.cpf_cnpj,
            request.email,
            request.phone,
            request.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return {"customer_id": customer_id}


@router.get("")
async def list_customers(
    customer_repo: CustomerRepo,
    principal: AdminPrincipal,
) -> list[CustomerResponse]:
    del principal
    use_case = ListCustomersUseCase(customer_repo)
    customers = await use_case.execute()
    return [
        CustomerResponse(
            id=str(c.id),
            name=c.name,
            cpf_cnpj=c.cpf_cnpj,
            email=c.email,
            phone=c.phone,
            is_active=c.is_active,
        )
        for c in customers
    ]


@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    customer_repo: CustomerRepo,
    principal: AdminPrincipal,
) -> CustomerResponse:
    del principal
    use_case = GetCustomerUseCase(customer_repo)
    customer = await use_case.execute(customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return CustomerResponse(
        id=str(customer.id),
        name=customer.name,
        cpf_cnpj=customer.cpf_cnpj,
        email=customer.email,
        phone=customer.phone,
        is_active=customer.is_active,
    )


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    request: CustomerUpdateRequest,
    customer_repo: CustomerRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = UpdateCustomerUseCase(customer_repo)
    try:
        ok = await use_case.execute(
            customer_id,
            request.name,
            request.cpf_cnpj,
            request.email,
            request.phone,
            request.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    customer_repo: CustomerRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = DeleteCustomerUseCase(customer_repo)
    ok = await use_case.execute(customer_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}
