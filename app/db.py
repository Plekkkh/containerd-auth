from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    create_engine,
    String,
    ForeignKey,
    Uuid,
    DateTime,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
    Session
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), unique=True)
    role: Mapped[str] = mapped_column(String(16), default="user")
    tokens_revoked_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

class ContainerOwnership(Base):
    __tablename__ = "container_ownership"

    container_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)


class ImageOwnership(Base):
    __tablename__ = "image_ownership"

    image_ref: Mapped[str] = mapped_column(String(256), primary_key=True, index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str | None] = mapped_column(String(128), nullable=True)
    result: Mapped[str] = mapped_column(String(16))  # "ok" | "denied" | "error"
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())


_engine = None
_SessionLocal: sessionmaker | None = None


def init_db(db_path_or_url: str) -> None:
    """
    Создать движок и таблицы. Вызывается один раз из create_app().

    :param db_path_or_url: Путь к sqlite-файлу или URL подключения.
    """

    global _engine, _SessionLocal

    if "://" in db_path_or_url:
        url = db_path_or_url
    else:
        url = f"sqlite:///{db_path_or_url}"

    connect_args = {
        "check_same_thread": False
    } if url.startswith("sqlite:///") else {}

    _engine = create_engine(url, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    Base.metadata.create_all(_engine)


def session_factory() -> Session:
    """Создать новую сессию SQLAlchemy."""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()


def get_db():
    """Cессия на время запроса."""
    db = session_factory()
    try:
        yield db
        db.commit()
    finally:
        db.close()
