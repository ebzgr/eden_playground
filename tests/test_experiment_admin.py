"""Experiment admin helpers."""

import pytest

from playground.services.admin.experiment_admin import (
    parse_arms_from_form,
    resolve_experiment_id,
    slugify_experiment_id,
)


def test_slugify_experiment_id():
    assert slugify_experiment_id("Deal Intro Test") == "exp_deal_intro_test"


def test_resolve_experiment_id_prefers_explicit():
    assert resolve_experiment_id("My Test", "exp_custom") == "exp_custom"


def test_resolve_experiment_id_from_name():
    assert resolve_experiment_id("My Test", "") == "exp_my_test"


def test_parse_arms_from_form_requires_two():
    with pytest.raises(ValueError, match="At least two"):
        parse_arms_from_form(["a"], ["base"], [1])
    arms = parse_arms_from_form(
        ["control", "urgent"], ["base", "urgent"], [50, 50]
    )
    assert len(arms) == 2
    assert arms[0]["version"] == "base"
