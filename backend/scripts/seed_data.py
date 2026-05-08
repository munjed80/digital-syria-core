from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models.admin_scope import District, Governorate, Municipality, Neighborhood
from app.models.base import Base
from app.models.population import (
    ChangeRequestStatus,
    ChangeRequestType,
    Gender,
    Household,
    HouseholdVerificationStatus,
    Person,
    PopulationChangeRequest,
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
        child = Person(
            household_id=household.id,
            full_name="ابن رب الأسرة التجريبي",
            gender=Gender.male,
            relation_to_head=RelationToHead.child,
        )
        db.add_all([head_person, spouse, child])
        db.flush()
        household.head_person_id = head_person.id


def seed_change_requests(db: Session) -> None:
    """Seed sample population change requests covering several states.

    Idempotent — keyed off the deterministic `request_number` values it
    assigns. Requires `seed_population` to have run first.
    """
    household = db.scalar(select(Household).where(Household.code == "HH-DEMO-001"))
    if household is None:
        return
    head = db.scalar(select(User).where(User.email == "head@demo.sy"))
    chief = db.scalar(select(User).where(User.email == "muni@demo.sy"))
    if head is None or chief is None:
        return

    members = list(db.scalars(select(Person).where(Person.household_id == household.id)))
    spouse = next(
        (p for p in members if p.relation_to_head == RelationToHead.spouse), None
    )
    child = next(
        (p for p in members if p.relation_to_head == RelationToHead.child), None
    )

    samples = [
        {
            "request_number": "CR-DEMO-000001",
            "request_type": ChangeRequestType.birth,
            "status": ChangeRequestStatus.submitted,
            "target": None,
            "payload": {
                "full_name": "مولود تجريبي",
                "gender": "female",
                "relation_to_head": "child",
                "birth_date": "2026-03-15",
            },
            "reason": "تسجيل ولادة جديدة",
            "is_approved": False,
            "is_rejected": False,
        },
        {
            "request_number": "CR-DEMO-000002",
            "request_type": ChangeRequestType.death,
            "status": ChangeRequestStatus.submitted,
            "target": spouse,
            "payload": {"death_date": "2026-04-01"},
            "reason": "تسجيل وفاة",
            "is_approved": False,
            "is_rejected": False,
        },
        {
            "request_number": "CR-DEMO-000003",
            "request_type": ChangeRequestType.correction,
            "status": ChangeRequestStatus.rejected,
            "target": child,
            "payload": {"full_name": "اسم مصحح"},
            "reason": "تصحيح اسم",
            "rejection_reason": "وثائق غير كافية",
            "is_approved": False,
            "is_rejected": True,
        },
        {
            "request_number": "CR-DEMO-000004",
            "request_type": ChangeRequestType.address_change,
            "status": ChangeRequestStatus.approved,
            "target": None,
            "payload": {"address_line": "حي المزة 86 — شارع 5 — بناء 7"},
            "reason": "انتقال السكن",
            "is_approved": True,
            "is_rejected": False,
        },
    ]

    from datetime import datetime, timezone

    for sample in samples:
        existing = db.scalar(
            select(PopulationChangeRequest).where(
                PopulationChangeRequest.request_number == sample["request_number"]
            )
        )
        if existing is not None:
            continue
        cr = PopulationChangeRequest(
            request_number=sample["request_number"],
            request_type=sample["request_type"],
            status=sample["status"],
            submitted_by_user_id=head.id,
            household_id=household.id,
            target_person_id=sample["target"].id if sample["target"] is not None else None,
            payload=sample["payload"],
            reason=sample["reason"],
        )
        if sample["is_rejected"]:
            cr.reviewed_by_user_id = chief.id
            cr.reviewed_at = datetime.now(timezone.utc)
            cr.rejection_reason = sample.get("rejection_reason")
        if sample["is_approved"]:
            cr.reviewed_by_user_id = chief.id
            cr.reviewed_at = datetime.now(timezone.utc)
            cr.approved_by_user_id = chief.id
            cr.approved_at = datetime.now(timezone.utc)
            # Materialise the address change for realism.
            if cr.request_type == ChangeRequestType.address_change:
                household.address_line = sample["payload"]["address_line"]
        db.add(cr)


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        seed_users(db)
        seed_services(db)
        seed_population(db)
        db.flush()
        seed_change_requests(db)
        db.commit()

    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()
