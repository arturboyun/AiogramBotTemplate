import logging
from typing import Generic, Iterable, Sequence, TypeVar

from sqlalchemy import Select, UnaryExpression, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from bot.models.base import Base

logger = logging.getLogger("Service")
TModel = TypeVar("TModel", bound=type[Base])


class Service(Generic[TModel]):
    model: TModel
    options: Iterable[ExecutableOption] | ExecutableOption | None

    def _build_get_query(
        self,
        *filters,
        limit: int | None = 1000,
        offset: int | None = None,
        options: Iterable[ExecutableOption] | ExecutableOption | None = None,
        stmt: Select | None = None,
        **filters_by,
    ) -> Select:
        if offset is None:
            offset = 0

        if stmt is None:
            stmt = select(self.model)
        if not isinstance(stmt, Select):
            raise TypeError("stmt must be a Select object")

        logger.debug(f"Building query for {self.model.__name__}")

        if options is True:
            options = self.options

        if options is not None:
            if isinstance(options, Iterable) and not isinstance(options, ExecutableOption):
                stmt = stmt.options(*options)
            else:
                stmt = stmt.options(options)

        if filters:
            stmt = stmt.filter(*filters)
        if filters_by:
            stmt = stmt.filter_by(**filters_by)

        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return stmt

    async def get_all(
        self,
        session: AsyncSession,
        *filters,
        limit: int | None = 1000,
        offset: int = 0,
        options: Iterable[ExecutableOption] | ExecutableOption | None | bool = None,
        order_by: UnaryExpression[TModel] | None = None,
        **filters_by,
    ) -> Sequence[TModel]:
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=limit, offset=offset, options=options, **filters_by
        )
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def get_count(
        self,
        session: AsyncSession,
        *filters,
        **filters_by,
    ) -> int:
        stmt = select(func.count(self.model.id))
        stmt = self._build_get_query(
            *filters, limit=None, offset=None, stmt=stmt, **filters_by
        )
        result = await session.execute(stmt)
        return result.scalar()

    async def get(
        self,
        session: AsyncSession,
        *filters,
        options: Iterable[ExecutableOption] | ExecutableOption | bool | None = None,
        **filters_by,
    ) -> TModel | None:
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=None, options=options, **filters_by
        )
        result = await session.execute(stmt)
        return result.unique().scalars().first()

    async def get_for_update(
        self,
        session: AsyncSession,
        *filters,
        options: Iterable[ExecutableOption] | ExecutableOption | bool | None = None,
        **filters_by,
    ) -> TModel | None:
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=None, offset=None, options=options, **filters_by
        )
        result = await session.execute(stmt.with_for_update())
        return result.scalar_one_or_none()

    async def add(self, session: AsyncSession, **kwargs) -> TModel:
        user_app = self.model(**kwargs)
        session.add(user_app)

        return user_app

    async def update(self, session: AsyncSession, obj: TModel, **kwargs) -> TModel:
        for key, value in kwargs.items():
            setattr(obj, key, value)

        return obj

    async def delete(self, session: AsyncSession, obj: TModel) -> None:
        await session.delete(obj)

    def asc(self, column_name: str) -> UnaryExpression[TModel]:
        if not getattr(self.model, column_name):
            raise ValueError(f"Column {column_name} not found in model {self.model}")
        return asc(getattr(self.model, column_name))

    def desc(self, column_name: str) -> UnaryExpression[TModel]:
        if not getattr(self.model, column_name):
            raise ValueError(f"Column {column_name} not found in model {self.model}")
        return desc(getattr(self.model, column_name))
