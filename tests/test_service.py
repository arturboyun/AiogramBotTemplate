import asyncio
import pytest
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, load_only

from bot.common.service import Service


class Base(DeclarativeBase):
    pass


class DummyModel(Base):
    __tablename__ = "dummy"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class DummyService(Service[type[DummyModel]]):
    model = DummyModel
    options = (load_only(DummyModel.id),)


class FakeResult:
    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return []

    def first(self):
        return None

    def scalar(self):
        return 0

    def scalar_one_or_none(self):
        return None


class FakeSession:
    def __init__(self):
        self.stmt = None

    async def execute(self, stmt):
        self.stmt = stmt
        return FakeResult()

    async def delete(self, obj):
        pass


@pytest.fixture
def service():
    return DummyService()


@pytest.fixture
def session():
    return FakeSession()


def test_default_options_with_boolean_true(service, session):
    asyncio.run(service.get_all(session, options=True))
    assert session.stmt._with_options == tuple(service.options)


def test_custom_option_preserved(service, session):
    custom_opt = load_only(DummyModel.name)
    asyncio.run(service.get_all(session, options=custom_opt))
    assert session.stmt._with_options == (custom_opt,)
