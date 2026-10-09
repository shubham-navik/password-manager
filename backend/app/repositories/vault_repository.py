from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vault_item import VaultItem


class VaultRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: UUID,
        data: dict,
    ) -> VaultItem:
        item = VaultItem(
            user_id=user_id,
            **data,
        )

        db.add(item)
        await db.commit()
        await db.refresh(item)

        return item

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID,
    ) -> VaultItem | None:
        result = await db.execute(
            select(VaultItem).where(
                VaultItem.id == item_id,
                VaultItem.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[VaultItem]:
        result = await db.execute(
            select(VaultItem)
            .where(VaultItem.user_id == user_id)
            .order_by(VaultItem.updated_at.desc())
        )

        return list(result.scalars().all())

    @staticmethod
    async def update(
        db: AsyncSession,
        item: VaultItem,
        data: dict,
    ) -> VaultItem:
        for field, value in data.items():
            setattr(item, field, value)

        await db.commit()
        await db.refresh(item)

        return item

    @staticmethod
    async def delete(
        db: AsyncSession,
        item: VaultItem,
    ) -> None:
        await db.delete(item)
        await db.commit()