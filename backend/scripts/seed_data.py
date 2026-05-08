from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.admin_scope import District, Governorate, Municipality, Neighborhood
from app.models.base import Base
from app.models.population import (
    Gender,
    Household,
    HouseholdVerificationStatus,
    Person,
    RelationToHead,
)
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


def seed_population(db: Session) -> None:
    """Seed administrative scope tree and demo population accounts.

    Creates: 1 governorate, 1 municipality, 1 district, 1 neighborhood; one
    user per role (super_admin, governor, municipality_chief, mukhtar,
    household_head); one verified household with two persons.
    """
    governorate = db.scalar(select(Governorate).where(Governorate.code == "SY-DI"))
    if governorate is None:
        governorate = Governorate(code="SY-DI", name_ar="دمشق")
        db.add(governorate)
        db.flush()

    municipality = db.scalar(select(Municipality).where(Municipality.code == "SY-DI-MZH"))
    if municipality is None:
        municipality = Municipality(
            governorate_id=governorate.id, code="SY-DI-MZH", name_ar="المزة"
        )
        db.add(municipality)
        db.flush()

    district = db.scalar(select(District).where(District.code == "SY-DI-MZH-D1"))
    if district is None:
        district = District(
            municipality_id=municipality.id, code="SY-DI-MZH-D1", name_ar="منطقة المزة 1"
        )
        db.add(district)
        db.flush()

    neighborhood = db.scalar(select(Neighborhood).where(Neighborhood.code == "SY-DI-MZH-D1-N1"))
    if neighborhood is None:
        neighborhood = Neighborhood(
            district_id=district.id, code="SY-DI-MZH-D1-N1", name_ar="حي المزة 86"
        )
        db.add(neighborhood)
        db.flush()

    role_users = [
        ("المسؤول الوطني", "superadmin@demo.sy", UserRole.super_admin, {}),
        (
            "محافظ دمشق",
            "governor@demo.sy",
            UserRole.governor,
            {"governorate_id": governorate.id},
        ),
        (
            "رئيس بلدية المزة",
            "muni@demo.sy",
            UserRole.municipality_chief,
            {
                "governorate_id": governorate.id,
                "municipality_id": municipality.id,
            },
        ),
        (
            "مختار حي المزة 86",
            "mukhtar@demo.sy",
            UserRole.mukhtar,
            {
                "governorate_id": governorate.id,
                "municipality_id": municipality.id,
                "district_id": district.id,
                "neighborhood_id": neighborhood.id,
            },
        ),
        (
            "رب الأسرة التجريبي",
            "head@demo.sy",
            UserRole.household_head,
            {},
        ),
    ]
    created: dict[str, User] = {}
    for full_name, email, role, scope in role_users:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            created[email] = existing
            continue
        user = User(
            full_name=full_name,
            email=email,
            password_hash=get_password_hash("Passw0rd!"),
            role=role,
            **scope,
        )
        db.add(user)
        db.flush()
        created[email] = user

    mukhtar = created["mukhtar@demo.sy"]
    head = created["head@demo.sy"]

    household = db.scalar(select(Household).where(Household.code == "HH-DEMO-001"))
    if household is None:
        household = Household(
            code="HH-DEMO-001",
            address_line="حي المزة 86 — شارع 1 — بناء 3",
            governorate_id=governorate.id,
            municipality_id=municipality.id,
            district_id=district.id,
            neighborhood_id=neighborhood.id,
            assigned_mukhtar_user_id=mukhtar.id,
            head_user_id=head.id,
            verification_status=HouseholdVerificationStatus.verified,
        )
        db.add(household)
        db.flush()

        head_person = Person(
            household_id=household.id,
            full_name=head.full_name,
            gender=Gender.male,
            relation_to_head=RelationToHead.self,
        )
        spouse = Person(
            household_id=household.id,
            full_name="زوجة رب الأسرة التجريبي",
            gender=Gender.female,
            relation_to_head=RelationToHead.spouse,
        )
        db.add_all([head_person, spouse])
        db.flush()
        household.head_person_id = head_person.id


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        seed_users(db)
        seed_services(db)
        seed_population(db)
        db.commit()

    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()
