import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import QueryTimeoutError


class DWMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name: str) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values(self, table_name: str, column_name: str, limit: int):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return result.scalars().fetchall()

    async def get_db_info(self):
        result = await self.session.execute(text("select version()"))
        version = result.scalar()

        dialect = self.session.get_bind().dialect.name

        return {'version': version, 'dialect': dialect}

    async def validate_sql(self, sql: str, timeout_seconds: float = 15.0):
        try:
            async with asyncio.timeout(timeout_seconds):
                await self.session.execute(text(f"explain {sql}"))
        except TimeoutError as exc:
            raise QueryTimeoutError("SQL 执行计划生成超时") from exc

    async def execute_sql(self, sql: str, timeout_seconds: float = 15.0):
        try:
            async with asyncio.timeout(timeout_seconds):
                result = await self.session.execute(text(sql))
                return [dict(row) for row in result.mappings().fetchall()]
        except TimeoutError as exc:
            raise QueryTimeoutError() from exc
