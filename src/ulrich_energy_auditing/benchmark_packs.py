from __future__ import annotations

import re

from ulrich_energy_auditing.models import BenchmarkPack, BuildingProfile

BENCHMARK_PACKS: tuple[BenchmarkPack, ...] = (
    BenchmarkPack(
        pack_id="mixed-humid-residential-legacy",
        label="Mixed-Humid Residential Retrofit (Legacy Home)",
        region="mixed-humid",
        building_archetype="residential",
        vintage_label="legacy",
        description="Older Midwest and mixed-humid detached homes with typical retrofit opportunities.",
        high_performing_max_eui=28.0,
        solid_max_eui=36.0,
        improvement_ready_max_eui=44.0,
        attic_insulation_target_r=49,
        blower_door_target_ach50=4.0,
        duct_leakage_target_percent=8.0,
    ),
    BenchmarkPack(
        pack_id="mixed-humid-residential-modern",
        label="Mixed-Humid Residential Baseline (Modern Home)",
        region="mixed-humid",
        building_archetype="residential",
        vintage_label="modern",
        description="Newer mixed-humid homes with tighter envelopes and better insulation baselines.",
        high_performing_max_eui=22.0,
        solid_max_eui=30.0,
        improvement_ready_max_eui=38.0,
        attic_insulation_target_r=60,
        blower_door_target_ach50=3.0,
        duct_leakage_target_percent=6.0,
    ),
    BenchmarkPack(
        pack_id="cold-residential-legacy",
        label="Cold Climate Residential Retrofit (Legacy Home)",
        region="cold",
        building_archetype="residential",
        vintage_label="legacy",
        description="Northern heating-dominant homes where insulation and air sealing carry most of the load.",
        high_performing_max_eui=32.0,
        solid_max_eui=42.0,
        improvement_ready_max_eui=52.0,
        attic_insulation_target_r=60,
        blower_door_target_ach50=3.5,
        duct_leakage_target_percent=7.0,
    ),
    BenchmarkPack(
        pack_id="hot-humid-residential-legacy",
        label="Hot-Humid Residential Retrofit (Legacy Home)",
        region="hot-humid",
        building_archetype="residential",
        vintage_label="legacy",
        description="Southern cooling-dominant homes where attic load, humidity control, and duct losses matter most.",
        high_performing_max_eui=26.0,
        solid_max_eui=34.0,
        improvement_ready_max_eui=42.0,
        attic_insulation_target_r=38,
        blower_door_target_ach50=4.5,
        duct_leakage_target_percent=8.0,
    ),
    BenchmarkPack(
        pack_id="mixed-humid-small-office-legacy",
        label="Mixed-Humid Small Office Baseline (Legacy Building)",
        region="mixed-humid",
        building_archetype="small-office",
        vintage_label="legacy",
        description="Small office and light-commercial buildings with older rooftop or split-system equipment.",
        high_performing_max_eui=44.0,
        solid_max_eui=56.0,
        improvement_ready_max_eui=68.0,
        attic_insulation_target_r=38,
        blower_door_target_ach50=5.0,
        duct_leakage_target_percent=10.0,
    ),
    BenchmarkPack(
        pack_id="mixed-humid-small-office-modern",
        label="Mixed-Humid Small Office Baseline (Modern Building)",
        region="mixed-humid",
        building_archetype="small-office",
        vintage_label="modern",
        description="Newer small office buildings with better controls, tighter shells, and lower plug-load waste.",
        high_performing_max_eui=36.0,
        solid_max_eui=48.0,
        improvement_ready_max_eui=60.0,
        attic_insulation_target_r=49,
        blower_door_target_ach50=4.0,
        duct_leakage_target_percent=8.0,
    ),
    BenchmarkPack(
        pack_id="cold-small-office-legacy",
        label="Cold Climate Small Office Retrofit (Legacy Building)",
        region="cold",
        building_archetype="small-office",
        vintage_label="legacy",
        description="Heating-dominant small commercial buildings where shell losses and schedule drift drive bills.",
        high_performing_max_eui=48.0,
        solid_max_eui=60.0,
        improvement_ready_max_eui=72.0,
        attic_insulation_target_r=49,
        blower_door_target_ach50=4.5,
        duct_leakage_target_percent=9.0,
    ),
    BenchmarkPack(
        pack_id="hot-humid-small-office-legacy",
        label="Hot-Humid Small Office Retrofit (Legacy Building)",
        region="hot-humid",
        building_archetype="small-office",
        vintage_label="legacy",
        description="Cooling-heavy small offices where ventilation, humidity, and duct losses often dominate.",
        high_performing_max_eui=40.0,
        solid_max_eui=52.0,
        improvement_ready_max_eui=64.0,
        attic_insulation_target_r=38,
        blower_door_target_ach50=5.0,
        duct_leakage_target_percent=9.0,
    ),
)

_PACK_INDEX = {pack.pack_id: pack for pack in BENCHMARK_PACKS}

_STATE_REGION = {
    "AL": "hot-humid",
    "AR": "mixed-humid",
    "AZ": "hot-dry",
    "CA": "mixed-humid",
    "CO": "cold",
    "CT": "cold",
    "FL": "hot-humid",
    "GA": "hot-humid",
    "IA": "cold",
    "ID": "cold",
    "IL": "mixed-humid",
    "IN": "mixed-humid",
    "KS": "mixed-humid",
    "KY": "mixed-humid",
    "LA": "hot-humid",
    "MA": "cold",
    "MD": "mixed-humid",
    "ME": "cold",
    "MI": "cold",
    "MN": "cold",
    "MO": "mixed-humid",
    "MS": "hot-humid",
    "NC": "hot-humid",
    "ND": "cold",
    "NE": "cold",
    "NH": "cold",
    "NJ": "cold",
    "NM": "hot-dry",
    "NV": "hot-dry",
    "NY": "cold",
    "OH": "mixed-humid",
    "OK": "hot-humid",
    "PA": "cold",
    "RI": "cold",
    "SC": "hot-humid",
    "SD": "cold",
    "TN": "mixed-humid",
    "TX": "hot-humid",
    "UT": "hot-dry",
    "VA": "mixed-humid",
    "VT": "cold",
    "WI": "cold",
    "WV": "mixed-humid",
    "WY": "cold",
}

_ADDRESS_STATE_PATTERN = re.compile(r",\s*([A-Z]{2})\b")


def resolve_benchmark_pack(
    building: BuildingProfile,
    benchmark_pack_id: str | None = None,
) -> tuple[BenchmarkPack, str]:
    if benchmark_pack_id is not None:
        try:
            pack = _PACK_INDEX[benchmark_pack_id]
        except KeyError as exc:
            available = ", ".join(sorted(_PACK_INDEX))
            raise ValueError(
                f"Unknown benchmark pack '{benchmark_pack_id}'. Available pack IDs: {available}."
            ) from exc
        return pack, "Selected explicitly from the CLI benchmark-pack override."

    region = _infer_region(building.address)
    archetype = _infer_archetype(building.building_type)
    vintage = _infer_vintage(building.year_built)
    selected_id = f"{region}-{archetype}-{vintage}"

    pack = _PACK_INDEX.get(selected_id)
    if pack is None:
        fallback_id = f"mixed-humid-{archetype}-legacy"
        pack = _PACK_INDEX.get(fallback_id, _PACK_INDEX["mixed-humid-residential-legacy"])
        return (
            pack,
            f"Auto-selected fallback pack because no exact benchmark pack exists for "
            f"{region} / {archetype} / {vintage}.",
        )

    return (
        pack,
        f"Auto-selected from region={region}, archetype={archetype}, and vintage={vintage}.",
    )


def list_benchmark_packs() -> list[BenchmarkPack]:
    return list(BENCHMARK_PACKS)


def _infer_region(address: str) -> str:
    match = _ADDRESS_STATE_PATTERN.search(address.upper())
    if not match:
        return "mixed-humid"
    region = _STATE_REGION.get(match.group(1), "mixed-humid")
    if region == "hot-dry":
        return "mixed-humid"
    return region


def _infer_archetype(building_type: str) -> str:
    normalized = building_type.strip().lower()
    if any(token in normalized for token in ("office", "commercial", "retail", "store")):
        return "small-office"
    return "residential"


def _infer_vintage(year_built: int) -> str:
    return "modern" if year_built >= 2005 else "legacy"
