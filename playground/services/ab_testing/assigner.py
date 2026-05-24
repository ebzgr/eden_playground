"""Seeded-random weighted arm selection."""

from hashlib import blake2b

from playground.config import get_settings


def pick_arm(
    subject_id: str,
    experiment_id: str,
    arms: list[dict],
) -> dict:
    """
    Pick an arm by weighted bucket from deterministic hash.

    Each arm dict must have: id, weight, and either version or next_scene.
    """
    total = sum(int(a.get("weight", 1)) for a in arms)
    if total <= 0:
        raise ValueError("experiment arms must have positive total weight")

    settings = get_settings()
    salt = settings.server_salt.encode("utf-8")[:16].ljust(16, b"\0")
    digest = blake2b(
        f"{subject_id}:{experiment_id}".encode("utf-8"),
        salt=salt,
        digest_size=8,
    ).hexdigest()
    bucket = int(digest, 16) % total

    cumulative = 0
    for arm in arms:
        cumulative += int(arm.get("weight", 1))
        if bucket < cumulative:
            return arm
    return arms[-1]
