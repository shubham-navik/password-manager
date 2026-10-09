from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.vault_repository import VaultRepository
from app.schemas.vault import (
    VaultItemCreate,
    VaultItemDetail,
    VaultItemSummary,
    VaultItemUpdate,
)
from app.security.encryption import (
    VaultEncryptionError,
    decrypt_value,
    encrypt_value,
)


class VaultService:

    @staticmethod
    async def create_item(
        db: AsyncSession,
        user_id: UUID,
        payload: VaultItemCreate,
    ) -> VaultItemDetail:
        data = {
            "title": payload.title,
            "website_url": payload.website_url,
            "username": payload.username,
            "encrypted_password": encrypt_value(payload.password),
            "encrypted_notes": (
                encrypt_value(payload.notes)
                if payload.notes is not None
                else None
            ),
        }

        item = await VaultRepository.create(
            db=db,
            user_id=user_id,
            data=data,
        )

        return VaultService._to_detail(item)

    @staticmethod
    async def list_items(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[VaultItemSummary]:
        items = await VaultRepository.list_by_user(
            db=db,
            user_id=user_id,
        )

        return [
            VaultItemSummary.model_validate(item)
            for item in items
        ]

    @staticmethod
    async def get_item(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID,
    ) -> VaultItemDetail:
        item = await VaultRepository.get_by_id(
            db=db,
            user_id=user_id,
            item_id=item_id,
        )

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vault item not found",
            )

        return VaultService._to_detail(item)

    @staticmethod
    async def update_item(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID,
        payload: VaultItemUpdate,
    ) -> VaultItemDetail:
        item = await VaultRepository.get_by_id(
            db=db,
            user_id=user_id,
            item_id=item_id,
        )

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vault item not found",
            )

        changes = payload.model_dump(exclude_unset=True)

        if "title" in changes and changes["title"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title cannot be null",
            )

        if "password" in changes:
            password = changes.pop("password")

            if password is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Password cannot be null",
                )

            changes["encrypted_password"] = encrypt_value(password)

        if "notes" in changes:
            notes = changes.pop("notes")

            changes["encrypted_notes"] = (
                encrypt_value(notes)
                if notes is not None
                else None
            )

        item = await VaultRepository.update(
            db=db,
            item=item,
            data=changes,
        )

        return VaultService._to_detail(item)

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID,
    ) -> None:
        item = await VaultRepository.get_by_id(
            db=db,
            user_id=user_id,
            item_id=item_id,
        )

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vault item not found",
            )

        await VaultRepository.delete(db, item)

    @staticmethod
    def _to_detail(item) -> VaultItemDetail:
        try:
            password = decrypt_value(item.encrypted_password)

            notes = (
                decrypt_value(item.encrypted_notes)
                if item.encrypted_notes is not None
                else None
            )

        except (VaultEncryptionError, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vault item could not be decrypted",
            ) from exc

        return VaultItemDetail(
            id=item.id,
            title=item.title,
            website_url=item.website_url,
            username=item.username,
            created_at=item.created_at,
            updated_at=item.updated_at,
            password=password,
            notes=notes,
        )