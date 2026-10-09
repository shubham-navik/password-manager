from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from app.api.rate_limit_dependencies import limit_by_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.vault import (
    VaultItemCreate,
    VaultItemDetail,
    VaultItemSummary,
    VaultItemUpdate,
)
from app.services.vault_service import VaultService


router = APIRouter(
    prefix="/api/v1/vault",
    tags=["Vault"],
    dependencies=[Depends(limit_by_user)],
)


@router.post(
    "",
    response_model=VaultItemDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_vault_item(
    payload: VaultItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await VaultService.create_item(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.get(
    "",
    response_model=list[VaultItemSummary],
)
async def list_vault_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await VaultService.list_items(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{item_id}",
    response_model=VaultItemDetail,
)
async def get_vault_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await VaultService.get_item(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
    )


@router.patch(
    "/{item_id}",
    response_model=VaultItemDetail,
)
async def update_vault_item(
    item_id: UUID,
    payload: VaultItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await VaultService.update_item(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
        payload=payload,
    )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_vault_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await VaultService.delete_item(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)