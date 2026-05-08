"""RBAC scoping helpers for the population registry.

Encapsulates the rules:
  * super_admin / admin → all of Syria
  * governor → only households in their governorate
  * municipality_chief → only households in their municipality
  * mukhtar → only households assigned to them, OR within their
    district / neighborhood scope
  * household_head → only their own household
  * citizen / employee / supervisor → no implicit population access
"""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.models.population import Household
from app.models.user import User, UserRole

# Roles that are allowed any read access at all to the population registry.
POPULATION_READ_ROLES = {
    UserRole.super_admin,
    UserRole.admin,
    UserRole.governor,
    UserRole.municipality_chief,
    UserRole.mukhtar,
    UserRole.household_head,
}

# Roles that may approve change requests at the mukhtar review stage.
MUKHTAR_REVIEW_ROLES = {UserRole.mukhtar}

# Roles that may approve change requests at the municipality review stage.
MUNICIPALITY_REVIEW_ROLES = {
    UserRole.municipality_chief,
    UserRole.governor,
    UserRole.super_admin,
    UserRole.admin,
}

# Roles that are permitted to administer households / persons directly
# (bypassing the change-request workflow). Citizens / household heads must
# use change requests.
DIRECT_REGISTRY_WRITE_ROLES = {
    UserRole.super_admin,
    UserRole.admin,
    UserRole.governor,
    UserRole.municipality_chief,
}


def is_national_role(role: UserRole) -> bool:
    return role in {UserRole.super_admin, UserRole.admin}


def household_visible_to(user: User, household: Household) -> bool:
    """Return True when `user` may read / list `household`."""
    role = user.role
    if role not in POPULATION_READ_ROLES:
        return False
    if is_national_role(role):
        return True
    if role == UserRole.governor:
        return (
            user.governorate_id is not None
            and household.governorate_id == user.governorate_id
        )
    if role == UserRole.municipality_chief:
        return (
            user.municipality_id is not None
            and household.municipality_id == user.municipality_id
        )
    if role == UserRole.mukhtar:
        if household.assigned_mukhtar_user_id == user.id:
            return True
        if user.neighborhood_id is not None:
            return household.neighborhood_id == user.neighborhood_id
        if user.district_id is not None:
            return household.district_id == user.district_id
        return False
    if role == UserRole.household_head:
        return household.head_user_id == user.id
    return False


def apply_household_scope(query: Select, user: User) -> Select:
    """Apply the household-visibility filter to a SELECT on Household."""
    role = user.role
    if is_national_role(role):
        return query
    if role == UserRole.governor:
        return query.where(Household.governorate_id == (user.governorate_id or -1))
    if role == UserRole.municipality_chief:
        return query.where(Household.municipality_id == (user.municipality_id or -1))
    if role == UserRole.mukhtar:
        clauses = [Household.assigned_mukhtar_user_id == user.id]
        if user.neighborhood_id is not None:
            clauses.append(Household.neighborhood_id == user.neighborhood_id)
        elif user.district_id is not None:
            clauses.append(Household.district_id == user.district_id)
        return query.where(or_(*clauses))
    if role == UserRole.household_head:
        return query.where(Household.head_user_id == user.id)
    # Any other role: explicitly produce zero rows.
    return query.where(Household.id == -1)


# Change-request types that are considered higher-risk and therefore
# require municipality_chief (or higher) approval after the mukhtar review.
HIGH_RISK_CHANGE_TYPES = {
    "address_change",
    "death",
    "remove_member",
    "correction",
}
