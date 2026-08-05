"""Normative advice specification coverage checks."""

import re
from collections import Counter
from pathlib import Path

import pytest

SPEC_PATH = Path(__file__).parents[5] / "docs/product/personalized-financial-advice-spec.md"
SCENARIO_OWNERS = {f"S-{index:02d}" for index in range(1, 9)}
VARIANT_OWNERS = {
    "V-PROV",
    "V-TRANS",
    "V-FLOW-DOWN",
    "V-FLOW-UP",
    "V-ONEOFF",
    "V-STOCK",
    "V-CHOICE",
    "V-REOPEN",
    "V-FRESH",
}


def test_normative_registry_assigns_69_requirements_once() -> None:
    """Inventory and both matrices keep one owner per normative requirement."""
    specification = SPEC_PATH.read_text(encoding="utf-8")
    inventory_text, registry_and_inverse = specification.split("### 7.2 Registre de couverture primaire", 1)
    registry_text, inverse_text = registry_and_inverse.split("### 7.3 Matrice inverse par propriétaire", 1)
    inventory = re.findall(
        r"^\| \*\*((?:(?:F|T|Q|E|ABS|X)-\d{2}|SIG-[AR]\d{2}))\*\* \|",
        inventory_text,
        re.MULTILINE,
    )
    registry = re.findall(
        r"^\| ((?:(?:F|T|Q|E|ABS|X)-\d{2}|SIG-[AR]\d{2})) \| [^|]+ \| [^|]+ \| "
        r"(S-\d{2}|V-[A-Z-]+) \|",
        registry_text,
        re.MULTILINE,
    )
    inverse_rows = re.findall(
        r"^\| (S-\d{2}|V-[A-Z-]+) \| ([A-Z0-9, -]+) \|$",
        inverse_text,
        re.MULTILINE,
    )
    inverse = [
        (requirement, owner)
        for owner, requirements in inverse_rows
        for requirement in requirements.split(", ")
    ]

    assert len(inventory) == 69
    assert Counter(inventory) == Counter(requirement for requirement, _ in registry)
    assert Counter(registry) == Counter(inverse)
    assert {owner for _, owner in registry} == SCENARIO_OWNERS | VARIANT_OWNERS


def test_all_canonical_scenarios_and_variants_have_end_to_end_owners(
    request: pytest.FixtureRequest,
) -> None:
    """Full-suite collection links every scenario and variant to integration coverage."""
    marked_items = [
        (item, owner)
        for item in request.session.items
        for marker in item.iter_markers("normative_scenarios")
        for owner in marker.args
    ]
    if not marked_items:
        pytest.skip("requires full-suite collection")

    assert {owner for _, owner in marked_items} == SCENARIO_OWNERS | VARIANT_OWNERS
    assert all("integration" in item.path.parts for item, _ in marked_items)
