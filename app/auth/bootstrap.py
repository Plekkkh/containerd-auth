from app.auth.passwords import hash_password
from app.config import Settings
from app.db import session_factory, User


def ensure_bootstrap_admin(settings: Settings) -> None:
    """Создать admin-аккаунт из env, если его ещё нет"""
    username = settings.ADMIN_USERNAME
    password = settings.ADMIN_PASSWORD
    if not username or not password:
        return

    db = session_factory()
    try:
        existing = db.query(User).filter_by(username=username).first()
        if existing is not None:
            return
        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                role="admin",
            )
        )
        db.commit()
    finally:
        db.close()
