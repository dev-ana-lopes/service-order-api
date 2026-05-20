from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ....application.use_cases.catalog_use_cases import (
    CreateCatalogServiceUseCase,
    CreateInventoryPartUseCase,
    DeleteCatalogServiceUseCase,
    DeleteInventoryPartUseCase,
    GetCatalogServiceUseCase,
    GetInventoryPartUseCase,
    ListCatalogServicesUseCase,
    ListInventoryPartsUseCase,
    UpdateCatalogServiceUseCase,
    UpdateInventoryPartUseCase,
)
from ....domain.contracts.token_verifier import AuthenticatedPrincipal
from ....domain.repositories import CatalogServiceRepository, InventoryPartRepository
from ....presentation.dependencies.auth import require_admin_principal
from ....presentation.dependencies.db_dependencies import (
    get_catalog_service_repository,
    get_inventory_part_repository,
)
from ....presentation.schemas.admin_schema import (
    CatalogServiceCreateRequest,
    CatalogServiceResponse,
    CatalogServiceUpdateRequest,
    InventoryPartCreateRequest,
    InventoryPartResponse,
    InventoryPartUpdateRequest,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])

CatalogServiceRepo = Annotated[
    CatalogServiceRepository, Depends(get_catalog_service_repository)
]
InventoryPartRepo = Annotated[
    InventoryPartRepository, Depends(get_inventory_part_repository)
]
AdminPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_admin_principal)]


@router.post("/services", status_code=status.HTTP_201_CREATED)
async def create_catalog_service(
    request: CatalogServiceCreateRequest,
    repo: CatalogServiceRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = CreateCatalogServiceUseCase(repo)
    service_id = await use_case.execute(request.description, request.price)
    return {"service_id": service_id}


@router.get("/services")
async def list_catalog_services(
    repo: CatalogServiceRepo,
    principal: AdminPrincipal,
) -> list[CatalogServiceResponse]:
    del principal
    use_case = ListCatalogServicesUseCase(repo)
    services = await use_case.execute()
    return [
        CatalogServiceResponse(id=str(s.id), description=s.description, price=s.price)
        for s in services
    ]


@router.get("/services/{service_id}")
async def get_catalog_service(
    service_id: UUID,
    repo: CatalogServiceRepo,
    principal: AdminPrincipal,
) -> CatalogServiceResponse:
    del principal
    use_case = GetCatalogServiceUseCase(repo)
    service = await use_case.execute(service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return CatalogServiceResponse(
        id=str(service.id),
        description=service.description,
        price=service.price,
    )


@router.put("/services/{service_id}")
async def update_catalog_service(
    service_id: UUID,
    request: CatalogServiceUpdateRequest,
    repo: CatalogServiceRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = UpdateCatalogServiceUseCase(repo)
    ok = await use_case.execute(service_id, request.description, request.price)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}


@router.delete("/services/{service_id}")
async def delete_catalog_service(
    service_id: UUID,
    repo: CatalogServiceRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = DeleteCatalogServiceUseCase(repo)
    ok = await use_case.execute(service_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}


@router.post("/parts", status_code=status.HTTP_201_CREATED)
async def create_inventory_part(
    request: InventoryPartCreateRequest,
    repo: InventoryPartRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = CreateInventoryPartUseCase(repo)
    try:
        part_id = await use_case.execute(
            request.name, request.unit_price, request.stock_quantity
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return {"part_id": part_id}


@router.get("/parts")
async def list_inventory_parts(
    repo: InventoryPartRepo,
    principal: AdminPrincipal,
) -> list[InventoryPartResponse]:
    del principal
    use_case = ListInventoryPartsUseCase(repo)
    parts = await use_case.execute()
    return [
        InventoryPartResponse(
            id=str(p.id),
            name=p.name,
            unit_price=p.unit_price,
            stock_quantity=p.stock_quantity,
        )
        for p in parts
    ]


@router.get("/parts/{part_id}")
async def get_inventory_part(
    part_id: UUID,
    repo: InventoryPartRepo,
    principal: AdminPrincipal,
) -> InventoryPartResponse:
    del principal
    use_case = GetInventoryPartUseCase(repo)
    part = await use_case.execute(part_id)
    if part is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return InventoryPartResponse(
        id=str(part.id),
        name=part.name,
        unit_price=part.unit_price,
        stock_quantity=part.stock_quantity,
    )


@router.put("/parts/{part_id}")
async def update_inventory_part(
    part_id: UUID,
    request: InventoryPartUpdateRequest,
    repo: InventoryPartRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = UpdateInventoryPartUseCase(repo)
    try:
        ok = await use_case.execute(
            part_id, request.name, request.unit_price, request.stock_quantity
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}


@router.delete("/parts/{part_id}")
async def delete_inventory_part(
    part_id: UUID,
    repo: InventoryPartRepo,
    principal: AdminPrincipal,
) -> dict:
    del principal
    use_case = DeleteInventoryPartUseCase(repo)
    ok = await use_case.execute(part_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {"success": True}
