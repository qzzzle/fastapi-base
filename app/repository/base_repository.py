from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Callable, Generic, Type, TypeVar

from pydantic import BaseModel as PydanticModel
from sqlalchemy import func, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.model.base_model import BaseModel as ORMBaseModel  # your SQLModel-derived base
from app.util.query_builder import dict_to_sqlalchemy_filter_options

M = TypeVar("M", bound=ORMBaseModel)


class BaseRepository(Generic[M]):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model: Type[M]) -> None:
        self.session_factory = session_factory
        self.model = model

    # ---------- READ ----------
    def read_by_options(
        self,
        schema: PydanticModel,
        *,
        eager: bool = False,
        with_deleted: bool = False,
    ) -> dict:
        schema_dict = schema.model_dump(exclude_none=True)

        # ordering
        ordering: str = schema_dict.get("ordering", configs.ORDERING)
        if ordering.startswith("-"):
            col_name = ordering[1:]
            col = getattr(self.model, col_name, None)
            order_clause = (col or getattr(self.model, configs.ORDERING.lstrip("-"))).desc()
        else:
            col = getattr(self.model, ordering, None)
            order_clause = (col or getattr(self.model, configs.ORDERING)).asc()

        # pagination
        page = int(schema_dict.get("page", configs.PAGE))
        page_size = schema_dict.get("page_size", configs.PAGE_SIZE)

        # filters (including your __lt/__gte style keys)
        filter_options = dict_to_sqlalchemy_filter_options(self.model, schema_dict)

        with self.session_factory() as session:
            query = session.query(self.model)
            if eager:
                for attr in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, attr)))

            if not with_deleted and hasattr(self.model, "deleted_at"):
                query = query.filter(self.model.deleted_at.is_(None))

            filtered_query = query.filter(filter_options)
            ordered_query = filtered_query.order_by(order_clause)

            if page_size == "all":
                items = ordered_query.all()
            else:
                ps = int(page_size)
                items = ordered_query.limit(ps).offset((page - 1) * ps).all()

            total_count = filtered_query.count()

            return {
                "founds": items,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

    def read_by_id(self, id: int, *, eager: bool = False, with_deleted: bool = False) -> M:
        with self.session_factory() as session:
            query = session.query(self.model)
            if eager:
                for attr in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, attr)))

            conditions = [self.model.id == id]
            if not with_deleted and hasattr(self.model, "deleted_at"):
                conditions.append(self.model.deleted_at.is_(None))

            obj = query.filter(*conditions).first()
            if not obj:
                raise NotFoundError(detail=f"not found id : {id}")
            return obj

    # ---------- CREATE ----------
    def create(self, schema: PydanticModel, *, created_by: int | None = None) -> M:
        # Remove server-managed / audit fields from payload
        payload = schema.model_dump(exclude_none=True)
        for k in ("id", "created_at", "modified_at", "deleted_at", "created_by", "modified_by", "deleted_by"):
            payload.pop(k, None)
        if created_by is not None and hasattr(self.model, "created_by"):
            payload["created_by"] = created_by

        with self.session_factory() as session:
            obj = self.model(**payload)
            try:
                session.add(obj)
                session.commit()
                session.refresh(obj)
            except IntegrityError as e:
                session.rollback()
                raise DuplicatedError(detail=str(e.orig))
            return obj

    # ---------- UPDATE (partial) ----------
    def update(self, id: int, schema: PydanticModel, *, modified_by: int | None = None) -> M:
        values = schema.model_dump(exclude_none=True)
        # Protect server-managed fields
        for k in ("id", "created_at", "deleted_at", "created_by", "deleted_by", "modified_at", "modified_by"):
            values.pop(k, None)

        # Ensure modified_at & modified_by are applied even with Core UPDATE
        if hasattr(self.model, "modified_at"):
            values["modified_at"] = func.now()
        if modified_by is not None and hasattr(self.model, "modified_by"):
            values["modified_by"] = modified_by

        with self.session_factory() as session:
            result = session.execute(
                sa_update(self.model)
                .where(self.model.id == id, self.model.deleted_at.is_(None))
                .values(**values)
            )
            if result.rowcount == 0:
                session.rollback()
                raise NotFoundError(detail=f"not found id : {id}")
            session.commit()
        return self.read_by_id(id)

    # ---------- UPDATE single attr ----------
    def update_attr(self, id: int, column: str, value: Any, *, modified_by: int | None = None) -> M:
        values: dict[str, Any] = {column: value}
        if hasattr(self.model, "modified_at"):
            values["modified_at"] = func.now()
        if modified_by is not None and hasattr(self.model, "modified_by"):
            values["modified_by"] = modified_by

        with self.session_factory() as session:
            result = session.execute(
                sa_update(self.model)
                .where(self.model.id == id, self.model.deleted_at.is_(None))
                .values(**values)
            )
            if result.rowcount == 0:
                session.rollback()
                raise NotFoundError(detail=f"not found id : {id}")
            session.commit()
        return self.read_by_id(id)

    # ---------- WHOLE UPDATE (replace) ----------
    def whole_update(self, id: int, schema: PydanticModel, *, modified_by: int | None = None) -> M:
        values = schema.model_dump()  # include explicit None to nullify fields on replace
        for k in ("id", "created_at", "deleted_at", "created_by", "deleted_by", "modified_at", "modified_by"):
            values.pop(k, None)

        if hasattr(self.model, "modified_at"):
            values["modified_at"] = func.now()
        if modified_by is not None and hasattr(self.model, "modified_by"):
            values["modified_by"] = modified_by

        with self.session_factory() as session:
            result = session.execute(
                sa_update(self.model)
                .where(self.model.id == id, self.model.deleted_at.is_(None))
                .values(**values)
            )
            if result.rowcount == 0:
                session.rollback()
                raise NotFoundError(detail=f"not found id : {id}")
            session.commit()
        return self.read_by_id(id)

    # ---------- DELETE ----------
    def delete_by_id(self, id: int, *, deleted_by: int | None = None, hard: bool = False) -> None:
        with self.session_factory() as session:
            if hard:
                obj = session.query(self.model).filter(self.model.id == id).first()
                if not obj:
                    raise NotFoundError(detail=f"not found id : {id}")
                session.delete(obj)
                session.commit()
                return

            # Soft delete
            values: dict[str, Any] = {"deleted_at": func.now()}
            if deleted_by is not None and hasattr(self.model, "deleted_by"):
                values["deleted_by"] = deleted_by

            result = session.execute(
                sa_update(self.model)
                .where(self.model.id == id, self.model.deleted_at.is_(None))
                .values(**values)
            )
            if result.rowcount == 0:
                session.rollback()
                raise NotFoundError(detail=f"not found id : {id}")
            session.commit()

    # ---------- SESSION ----------
    def close_scoped_session(self):
        with self.session_factory() as session:
            return session.close()
