"""Consent gate for event ingestion."""

from playground.models.user import User


def consent_allows_tracking(user: User) -> bool:
    return user.consent_state == "granted"
