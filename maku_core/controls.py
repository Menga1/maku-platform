"""
Rule-based safety controls, tagged for residual-risk calculation.
=================================================================
Single source of truth for the controls MAKU recommends (ai_advisor.py's
*_controls() functions return the .text of these). Each Control records:

  id        stable identifier (API clients send these back as "applied")
  text      the recommendation shown to people (unchanged wording)
  hazards   the risk_matrix hazard name(s) it reduces - exactly the names
            risk_engine.py passes to score_hazard(); a test checks this
  level     hierarchy of controls: elimination > engineering >
            administrative > ppe; "monitoring" for "keep monitoring"
            advice, which never reduces risk

No Streamlit, no I/O: safe to call from the web app, the API or a test.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

LEVELS = ("elimination", "engineering", "administrative", "ppe", "monitoring")

# Hazard names exactly as risk_engine.py scores them.
H_SOLAR_HEAT = "Perceived thermal temperature (heat/UV amplification)"
H_SOLAR_UV = "UV index"
H_HUMIDEX = "Humidex heat stress"
H_OFFSHORE_WIND = "Wind (crane/lifting)"
H_TUNNEL_HEAT = "Trapped-heat / geothermal humidity (perceived temp)"
H_CO = "Carbon monoxide (CO) OEL"
H_PM25 = "Respirable dust (PM2.5) OEL"
H_WIND_SHEAR = "Wind shear (crane gate)"
H_CRANE_LOAD = "Crane-load oscillation index"
H_ARC_FLASH = "Arc-flash incident energy"
H_AISLE = "Hot/cold-aisle thermal differential"
H_CONFINED = "Confined ceiling-void + armed clean-agent suppression"
H_HUB_WIND = "Hub-height wind speed (fall-from-height access gate)"
H_LIGHTNING = "Lightning (30-30 rule)"
H_CTV = "CTV transfer sea state (offshore)"
H_SILICA = "Respirable crystalline silica (RCS)"
H_NOISE = "Noise dose"
H_WBV = "Whole-body vibration A(8)"
H_TIDE = "Tide clearance margin"
H_NIGHT = "Night-time visibility"
H_CORROSION = "Splash-zone hardware corrosion capacity loss"
H_WBGT = "WBGT heat-strain (clothing- and workload-adjusted)"


@dataclass(frozen=True)
class Control:
    id: str
    text: str
    hazards: tuple[str, ...]
    level: str

    def __post_init__(self):
        if self.level not in LEVELS:
            raise ValueError(f"unknown control level {self.level!r}")

    def as_dict(self) -> dict:
        d = asdict(self)
        d["hazards"] = list(self.hazards)
        return d


def C(id_: str, text: str, hazards: tuple[str, ...] | list[str], level: str) -> Control:  # noqa: N802
    return Control(id_, text, tuple(hazards), level)


# --------------------------------------------------------------------- solar
def solar(result: dict) -> list[Control]:
    band = result["risk_band"]
    out = []
    heat = (H_SOLAR_HEAT, H_SOLAR_UV)
    if band in ("Moderate", "High", "Extreme"):
        out += [
            C("solar.reschedule", "Shift high-exertion tracker/module installation to early morning or late afternoon windows",
              heat, "administrative"),
            C("solar.work_rest", "Enforce ACGIH work/rest cycle per calculated action level; increase rest ratio if margin exceeded",
              (H_SOLAR_HEAT,), "administrative"),
            C("solar.cooling", "Mandatory shaded rest areas / cooling stations within 100m of active work fronts",
              heat, "engineering"),
            C("solar.buddy", "Buddy system + heat-illness spotters; mandatory electrolyte replacement schedule",
              (H_SOLAR_HEAT,), "administrative"),
        ]
    if band in ("High", "Extreme"):
        out += [
            C("solar.suspend_peak", "Escalate to HSE manager: consider suspending non-critical outdoor MEP tasks during peak GHI hours",
              heat, "elimination"),
            C("solar.reflective_ppe", "Reflective/ventilated PPE for crews working adjacent to panel rows (elevated radiant load)",
              heat, "ppe"),
        ]
    return out or [C("solar.monitor", "Maintain standard heat-safety protocol; monitor GHI/temp trend for escalation",
                     (), "monitoring")]


# ------------------------------------------------------------------ offshore
def offshore(result: dict) -> list[Control]:
    out = []
    band = result["risk_band"]
    if band in ("Moderate", "High", "Extreme"):
        out += [
            C("offshore.rotation", "Adjust welding/pipe-fitting shift rotations per Humidex band; shorten exposure intervals",
              (H_HUMIDEX,), "administrative"),
            C("offshore.hydration_ventilation",
              "Increase hydration monitoring; enclosed-space heat retention areas need forced ventilation checks",
              (H_HUMIDEX,), "administrative"),
        ]
    if result["wind_risk_status"] != "Normal Operations":
        out.append(C("offshore.wind_status", f"Wind risk status: {result['wind_risk_status']}", (), "monitoring"))
    if result["safety_override"]:
        out.insert(0, C("offshore.override", "SAFETY OVERRIDE: suspend crane/lifting and welding ops until conditions recheck",
                        (H_OFFSHORE_WIND, H_HUMIDEX), "elimination"))
    return out or [C("offshore.monitor", "Maintain standard marine HSE protocol; monitor wind/humidex trend", (), "monitoring")]


# --------------------------------------------------------------- underground
def underground(result: dict) -> list[Control]:
    out = []
    band = result["risk_band"]
    if result["safety_override"]:
        out.append(C("underground.override",
                     "SAFETY OVERRIDE: halt non-essential high-voltage MEP cabling work until conditions recheck",
                     (H_TUNNEL_HEAT, H_CO, H_PM25), "elimination"))
    if result["gas_exceeds"]:
        out.append(C("underground.co_evacuate",
                     "CO OEL exceeded - evacuate face area, verify forced ventilation, re-test before re-entry",
                     (H_CO,), "elimination"))
    if result["dust_exceeds"]:
        out.append(C("underground.dust",
                     "PM2.5 OEL exceeded - mandatory respiratory PPE upgrade, water suppression, re-test",
                     (H_PM25,), "engineering"))
    if band in ("MODERATE", "HIGH", "CRITICAL"):
        out.append(C("underground.work_rest",
                     "Reduce work/rest ratio for MEP electrical crews; rotate more frequently as heat trend rises",
                     (H_TUNNEL_HEAT,), "administrative"))
    if band in ("HIGH", "CRITICAL"):
        out.append(C("underground.temp_ventilation",
                     "Prioritize temporary ventilation deployment ahead of permanent system commissioning",
                     (H_TUNNEL_HEAT, H_CO, H_PM25), "engineering"))
    return out or [C("underground.monitor",
                     "Maintain standard underground HSE protocol; continue OEL and heat monitoring cadence", (), "monitoring")]


# ----------------------------------------------------------------- high-rise
def high_rise(result: dict) -> list[Control]:
    out = []
    band = result["risk_band"]
    if result["safety_override"]:
        out.append(C("high_rise.override",
                     "SAFETY OVERRIDE: suspend all crane lifts and external-wall/curtain-wall installation "
                     "until scaled wind drops below the 30-knot threshold",
                     (H_WIND_SHEAR, H_CRANE_LOAD), "elimination"))
    if band in ("HIGH", "CRITICAL"):
        out += [
            C("high_rise.notify_crane", "Notify tower crane operator and site HSE manager of current floor-level scaled wind readings",
              (H_WIND_SHEAR,), "administrative"),
            C("high_rise.recheck_rigging", "Recheck tie-off points and suspended-access rigging before resuming work at height",
              (H_CRANE_LOAD,), "administrative"),
        ]
    if band == "MODERATE":
        out.append(C("high_rise.delay_lifts", "Delay non-critical curtain-wall/riser lifts to the next confirmed calm window",
                     (H_WIND_SHEAR, H_CRANE_LOAD), "administrative"))
    return out or [C("high_rise.monitor",
                     "Maintain standard at-height wind-monitoring protocol; recheck anemometer feed each shift", (), "monitoring")]


# ---------------------------------------------------------------- data center
def data_center(result: dict) -> list[Control]:
    out = []
    if result["arc_flash_danger"]:
        out.append(C("data_center.de_energize",
                     "DANGER: arc-flash incident energy exceeds 40 cal/cm2 - "
                     "de-energize equipment before any work; no PPE category permits live work",
                     (H_ARC_FLASH,), "elimination"))
    if result.get("arc_flash_study_required") and result.get("energized_work_planned", True):
        out.append(C("data_center.unknown_ie_no_live_work",
                     "Arc-flash incident energy is UNKNOWN: no energized work until the equipment's arc-flash "
                     "label or a current arc-flash study (IEEE 1584) confirms incident energy and the required arc rating; "
                     "otherwise establish an electrically safe work condition (lock-out/tag-out, test before touch)",
                     (H_ARC_FLASH,), "elimination"))
    elif result.get("arc_flash_ppe") and not result["arc_flash_danger"] and result.get("arc_flash_energy_cal"):
        out.append(C("data_center.arc_ppe",
                     f"Arc-flash PPE for energized work: {result['arc_flash_ppe']} "
                     f"(source: {result.get('arc_flash_source', 'n/a')})",
                     (H_ARC_FLASH,), "ppe"))
    if result["confined_armed_danger"]:
        out.append(C("data_center.disarm_and_test",
                     "Confined ceiling-void space + armed clean-agent suppression: disarm/isolate "
                     "the system and atmosphere-test (O2/asphyxiant risk) before entry",
                     (H_CONFINED,), "engineering"))
    if result["thermal_differential"] >= 15.0:
        out.append(C("data_center.aisle_rotation",
                     "Hot/cold-aisle thermal differential elevated - rotate commissioning crews "
                     "more frequently, hydrate, reduce continuous hot-aisle dwell time",
                     (H_AISLE,), "administrative"))
    if result["safety_override"]:
        out.insert(0, C("data_center.override",
                        "SAFETY OVERRIDE: halt non-essential commissioning work in this zone until conditions are rechecked",
                        (H_ARC_FLASH, H_AISLE, H_CONFINED), "elimination"))
    return out or [C("data_center.monitor",
                     "Maintain standard data-center commissioning HSE protocol; continue thermal, arc-flash, and "
                     "confined-space monitoring cadence", (), "monitoring")]


# ---------------------------------------------------------------- wind energy
def wind_energy(result: dict) -> list[Control]:
    out = []
    if result["safety_override"]:
        out.append(C("wind_energy.override",
                     "SAFETY OVERRIDE: halt all blade/nacelle access and crane operations "
                     "until wind, lightning, or sea-state conditions clear",
                     (H_HUB_WIND, H_LIGHTNING, H_CTV), "elimination"))
    if "STOP WORK" in result["lightning_status"]:
        out.append(C("wind_energy.lightning_evacuate",
                     "30-30 rule triggered: evacuate exposed work-at-height positions immediately; "
                     "do not resume outdoor work until 30 minutes after the last observed strike",
                     (H_LIGHTNING,), "elimination"))
    if result["risk_band"] in ("HIGH", "CRITICAL") and "STOP WORK" not in result["lightning_status"]:
        out.append(C("wind_energy.restrict_access",
                     "Restrict blade/nacelle access to essential tasks only; recheck anemometer trend before each climb",
                     (H_HUB_WIND,), "administrative"))
    if result["is_offshore"] and "Suspended" in result["ctv_transfer_status"]:
        out.append(C("wind_energy.ctv_suspend",
                     "Suspend all crew-transfer-vessel personnel transfers until significant wave height drops below the transfer limit",
                     (H_CTV,), "elimination"))
    if result["is_offshore"] and "Restricted" in result["ctv_transfer_status"]:
        out.append(C("wind_energy.ctv_restrict",
                     "Limit CTV transfers to essential personnel only; brief crew on sea-state trend",
                     (H_CTV,), "administrative"))
    return out or [C("wind_energy.monitor",
                     "Maintain standard wind-energy HSE protocol; continue hub-height wind, lightning, and sea-state monitoring",
                     (), "monitoring")]


# ---------------------------------------------------------- mining/quarrying
def mining_quarrying(result: dict) -> list[Control]:
    out = []
    if result["safety_override"]:
        out.insert(0, C("mining.override",
                        "SAFETY OVERRIDE: halt exposure until silica, noise, or vibration levels are brought under control",
                        (H_SILICA, H_NOISE, H_WBV), "elimination"))
    if result["silica_exceeds_oel"]:
        out.append(C("mining.silica",
                     "Respirable crystalline silica exceeds the OEL - mandatory water suppression/wet-cutting, "
                     "upgrade respiratory PPE, rotate crews away from the quarry face",
                     (H_SILICA,), "engineering"))
    if result["noise_dose_pct"] >= 100:
        out.append(C("mining.noise",
                     f"Noise dose at {result['noise_dose_pct']}% of the permissible 8-hour limit - "
                     "mandatory hearing protection, reduce continuous exposure duration, isolate/enclose plant noise sources where feasible",
                     (H_NOISE,), "engineering"))
    if result["vibration_exceeds_limit"]:
        out.append(C("mining.vibration_remove",
                     "Whole-body vibration A(8) exceeds the EU exposure limit value - remove operator from "
                     "the machine immediately, inspect seat/suspension, reduce daily operating hours",
                     (H_WBV,), "elimination"))
    elif result["vibration_exceeds_action"]:
        out.append(C("mining.vibration_maintain",
                     "Whole-body vibration A(8) exceeds the action value - schedule maintenance on seat/suspension, monitor exposure hours",
                     (H_WBV,), "administrative"))
    return out or [C("mining.monitor",
                     "Maintain standard mining/quarrying HSE protocol; continue silica, noise, and vibration monitoring cadence",
                     (), "monitoring")]


# ---------------------------------------------------------------- marine port
def marine_port(result: dict) -> list[Control]:
    out = []
    if result["safety_override"]:
        out.insert(0, C("marine_port.override",
                        "SAFETY OVERRIDE: halt marine/port access work until tide clearance or hardware capacity conditions are rechecked",
                        (H_TIDE, H_NIGHT, H_CORROSION), "elimination"))
    if result["tide_clearance_margin_m"] <= 0.3:
        out.append(C("marine_port.tide_halt",
                     "Tide clearance margin critical - halt underside/pile-driving access work until tide recedes to a safe margin",
                     (H_TIDE,), "elimination"))
    elif result["tide_clearance_margin_m"] <= 0.8:
        out.append(C("marine_port.tide_restrict",
                     "Tide clearance margin restricted - limit access to essential monitored tasks, recheck tide tables before each shift",
                     (H_TIDE,), "administrative"))
    if result["night_amplified"]:
        out.append(C("marine_port.lighting",
                     "Task-area illuminance below the OSHA 1926.56 minimum for night operations - deploy additional lighting before resuming work",
                     (H_NIGHT,), "engineering"))
    if result["hardware_remaining_capacity_pct"] < 85.0:
        out.append(C("marine_port.hardware_inspect",
                     f"Splash-zone hardware estimated at {result['hardware_remaining_capacity_pct']}% of rated capacity - "
                     "schedule a certified structural inspection before continued use; consider derating safe working load",
                     (H_CORROSION,), "administrative"))
    return out or [C("marine_port.monitor",
                     "Maintain standard marine/port HSE protocol; continue tide, lighting, and hardware-condition monitoring",
                     (), "monitoring")]


# ---------------------------------------------------------------- heat stress
def heat_stress(result: dict) -> list[Control]:
    out = []
    if result["safety_override"]:
        if result.get("requires_physiological_monitoring"):
            out.insert(0, C("heat_stress.physiological_monitoring",
                            "SAFETY OVERRIDE: vapor-barrier/limited-use PPE requires direct physiological "
                            "monitoring (e.g. core temperature, heart-rate recovery) - a WBGT table lookup "
                            "alone is not sufficient authorization to continue work in this ensemble",
                            (H_WBGT,), "administrative"))
        else:
            out.insert(0, C("heat_stress.stop_work",
                            "STOP WORK: no ACGIH-compliant work/rest ratio exists at this workload/clothing/"
                            "acclimatization combination, even at 25/75 - reduce workload category, change "
                            "clothing, or wait for cooler conditions before resuming",
                            (H_WBGT,), "elimination"))
    elif result.get("recommended_work_rest_ratio") not in (None, "100/0"):
        out.append(C("heat_stress.work_rest",
                     f"Adopt a {result['recommended_work_rest_ratio']} work/rest cycle to stay within the ACGIH TLV "
                     f"action limit for this workload category and clothing ensemble",
                     (H_WBGT,), "administrative"))
    if not result.get("acclimatized"):
        out.append(C("heat_stress.acclimatize",
                     "Worker is not marked as heat-acclimatized - apply a graduated acclimatization schedule "
                     "(ACGIH recommends progressive exposure over ~1-2 weeks) before assigning full workload",
                     (H_WBGT,), "administrative"))
    return out or [C("heat_stress.monitor",
                     "Maintain standard heat-stress protocol; recheck WBGT/clothing/workload if conditions change",
                     (), "monitoring")]


RULES_BY_MODULE = {
    "Solar (Desert)": solar,
    "Offshore (Marine)": offshore,
    "Underground (Tunnel/Metro)": underground,
    "High-Rise (Vertical Urban)": high_rise,
    "Data Center (Controlled Critical Environment)": data_center,
    "Wind Energy (Onshore/Offshore)": wind_energy,
    "Mining & Quarrying": mining_quarrying,
    "Marine & Port Construction": marine_port,
    "Occupational Heat Stress (ISO 7243 / ACGIH TLV)": heat_stress,
}


def controls_for_result(result: dict) -> list[Control]:
    """The recommended controls for an engine result."""
    return RULES_BY_MODULE[result["module"]](result)


def resolve_applied(result: dict, applied: list[str]) -> list[Control]:
    """Maps what a person (or API client) marked as applied - control ids or
    the displayed texts - to the Control objects of THIS result. Anything
    that isn't one of this result's recommendations is ignored, so a client
    can't claim credit for a control MAKU never recommended."""
    wanted = set(applied or [])
    return [c for c in controls_for_result(result) if c.id in wanted or c.text in wanted]
