from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.service import ServiceCatalogItem
from app.models.user import User, UserRole


def seed_users(db: Session) -> None:
    demo_users = [
        ("مواطن تجريبي", "citizen@demo.sy", UserRole.citizen),
        ("موظف تجريبي", "employee@demo.sy", UserRole.employee),
        ("مشرف تجريبي", "supervisor@demo.sy", UserRole.supervisor),
        ("مدير النظام", "admin@demo.sy", UserRole.admin),
    ]

    for full_name, email, role in demo_users:
        exists = db.scalar(select(User).where(User.email == email))
        if exists:
            continue
        db.add(
            User(
                full_name=full_name,
                email=email,
                password_hash=get_password_hash("Passw0rd!"),
                role=role,
            )
        )


def seed_services(db: Session) -> None:
    demo_services = [
        (
            "CIVIL_001",
            "طلب قيد مدني",
            "خدمة تجريبية لتقديم طلبات القيد المدني ضمن الحوكمة الرقمية.",
        ),
        (
            "MUNI_001",
            "شكوى خدمية",
            "تقديم شكوى رسمية حول خدمات البلدية ومتابعة حالتها.",
        ),
    ]

    for code, title_ar, description_ar in demo_services:
        exists = db.scalar(select(ServiceCatalogItem).where(ServiceCatalogItem.code == code))
        if exists:
            continue
        db.add(ServiceCatalogItem(code=code, title_ar=title_ar, description_ar=description_ar))


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        seed_users(db)
        seed_services(db)
        db.commit()

    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()
