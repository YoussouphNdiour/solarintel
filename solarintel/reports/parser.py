"""
Parseur de la sortie CrewAI vers un SolarReport structuré.

Stratégie :
1. Cherche un bloc JSON embarqué (```json ... ```)
2. Fallback : extraction par regex des valeurs numériques clés
3. Défauts depuis constants.py pour les champs manquants
"""

from __future__ import annotations

import json
import re
from typing import Any

from solarintel.config.constants import (
    DEFAULT_LOCATION,
    DEFAULT_PANEL,
    ECONOMIC_DEFAULTS,
)
from solarintel.reports.models import (
    EconomicAnalysis,
    QAReport,
    QAValidation,
    SimulationResults,
    SolarReport,
    SystemConfig,
)


def parse_crew_output(
    raw_text: str,
    project: dict | None = None,
) -> SolarReport:
    """Parse la sortie brute de crew.kickoff() en SolarReport."""
    raw_text = str(raw_text)

    # Try JSON extraction first
    data = _extract_json(raw_text)
    if data:
        return _build_from_json(data, raw_text, project)

    # Fallback: regex extraction
    return _build_from_regex(raw_text, project)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict | None:
    """Extrait le premier bloc JSON trouvé dans le texte."""
    # Try ```json ... ``` blocks
    pattern = r"```json\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try raw JSON object
    pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and len(data) > 3:
                return data
        except json.JSONDecodeError:
            continue

    return None


def _build_from_json(
    data: dict,
    raw_text: str,
    project: dict | None,
) -> SolarReport:
    """Construit un SolarReport à partir de données JSON extraites."""
    loc = (project or {}).get("location", DEFAULT_LOCATION)
    panel = (project or {}).get("panel", DEFAULT_PANEL)

    # System config
    sys_data = data.get("system", data.get("configuration", {}))
    system = SystemConfig(
        panel_brand=sys_data.get("panel_brand", panel["brand"]),
        panel_model=sys_data.get("panel_model", panel["model"]),
        panel_power_wc=sys_data.get("panel_power_wc", panel["power_wc"]),
        panel_efficiency=sys_data.get("panel_efficiency", panel["efficiency"]),
        panel_count=sys_data.get("panel_count", 1),
        total_power_kwc=sys_data.get("total_power_kwc", 0.0),
        location_name=sys_data.get("location_name", loc["name"]),
        latitude=sys_data.get("latitude", loc["latitude"]),
        longitude=sys_data.get("longitude", loc["longitude"]),
        altitude=sys_data.get("altitude", loc["altitude"]),
        orientation_azimuth=sys_data.get("azimuth", 180.0),
        tilt=sys_data.get("tilt", 15.0),
    )

    # Simulation
    sim_data = data.get("simulation", data.get("production", {}))
    monthly = sim_data.get("monthly_production_kwh", [0.0] * 12)
    simulation = SimulationResults(
        annual_production_kwh=sim_data.get("annual_production_kwh", sum(monthly)),
        monthly_production_kwh=monthly,
        specific_yield_kwh_kwc=sim_data.get("specific_yield_kwh_kwc", 0.0),
        performance_ratio=sim_data.get("performance_ratio", 0.0),
        soiling_loss_pct=sim_data.get("soiling_loss_pct", 2.0),
        mismatch_loss_pct=sim_data.get("mismatch_loss_pct", 1.0),
        wiring_loss_pct=sim_data.get("wiring_loss_pct", 1.5),
        availability_loss_pct=sim_data.get("availability_loss_pct", 1.0),
        temperature_loss_pct=sim_data.get("temperature_loss_pct", 3.0),
        total_losses_pct=sim_data.get("total_losses_pct", 0.0),
    )

    # Economics
    eco_data = data.get("economics", data.get("economic_analysis", {}))
    economics = EconomicAnalysis(
        total_cost_xof=eco_data.get("total_cost_xof", 0.0),
        cost_per_kwc_xof=eco_data.get("cost_per_kwc_xof", 0.0),
        lcoe_xof_kwh=eco_data.get("lcoe_xof_kwh", 0.0),
        roi_pct=eco_data.get("roi_pct", 0.0),
        payback_years=eco_data.get("payback_years", 0.0),
        npv_xof=eco_data.get("npv_xof", 0.0),
        annual_savings_xof=eco_data.get("annual_savings_xof", 0.0),
        cashflow_cumulative=eco_data.get("cashflow_cumulative", [0.0] * 25),
    )

    # QA
    qa_data = data.get("qa", data.get("qa_report", {}))
    qa = _parse_qa(qa_data)

    return SolarReport(
        project_name=data.get("project_name", "Projet Solaire"),
        executive_summary=data.get("executive_summary", ""),
        system=system,
        simulation=simulation,
        economics=economics,
        qa=qa,
        raw_crew_output=raw_text,
    )


# ---------------------------------------------------------------------------
# Regex fallback
# ---------------------------------------------------------------------------

_FLOAT_RE = re.compile(r"[-+]?\d[\d\s]*[.,]?\d*")


def _find_float(text: str, pattern: str, default: float = 0.0) -> float:
    """Cherche un nombre après un pattern textuel."""
    full = r"(?:" + pattern + r")\s*[:=]?\s*([-+]?\d[\d\s]*[.,]?\d*)"
    match = re.search(full, text, re.I)
    if match and match.group(1):
        val_str = match.group(1).replace(" ", "").replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            pass
    return default


def _build_from_regex(raw_text: str, project: dict | None) -> SolarReport:
    """Extraction par regex quand aucun JSON n'est trouvé."""
    loc = (project or {}).get("location", DEFAULT_LOCATION)
    panel = (project or {}).get("panel", DEFAULT_PANEL)

    annual_kwh = _find_float(raw_text, r"production annuelle")
    pr = _find_float(raw_text, r"performance ratio|PR")
    if pr > 1:
        pr = pr / 100
    payback = _find_float(raw_text, r"payback|retour")
    lcoe = _find_float(raw_text, r"LCOE")
    total_cost = _find_float(raw_text, r"co[uû]t total")
    roi = _find_float(raw_text, r"ROI")
    n_panels = _find_float(raw_text, r"nombre de panneaux|panneaux")

    system = SystemConfig(
        panel_brand=panel["brand"],
        panel_model=panel["model"],
        panel_power_wc=panel["power_wc"],
        panel_efficiency=panel["efficiency"],
        panel_count=int(n_panels) if n_panels else 1,
        total_power_kwc=(n_panels * panel["power_wc"] / 1000) if n_panels else 0,
        location_name=loc["name"],
        latitude=loc["latitude"],
        longitude=loc["longitude"],
        altitude=loc["altitude"],
    )

    simulation = SimulationResults(
        annual_production_kwh=annual_kwh,
        performance_ratio=pr,
    )

    economics = EconomicAnalysis(
        total_cost_xof=total_cost,
        lcoe_xof_kwh=lcoe,
        roi_pct=roi,
        payback_years=payback,
    )

    return SolarReport(
        system=system,
        simulation=simulation,
        economics=economics,
        raw_crew_output=raw_text,
    )


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------

def _parse_qa(qa_data: dict) -> QAReport:
    """Parse les données QA en QAReport."""
    validations = []
    for v in qa_data.get("validations", []):
        if isinstance(v, dict):
            validations.append(QAValidation(
                code=v.get("code", "V?"),
                label=v.get("label", ""),
                status=v.get("status", "PASS"),
                detail=v.get("detail", ""),
            ))

    edge_cases = []
    for ec in qa_data.get("edge_cases", []):
        if isinstance(ec, dict):
            edge_cases.append(QAValidation(
                code=ec.get("code", "EC?"),
                label=ec.get("label", ""),
                status=ec.get("status", "PASS"),
                detail=ec.get("detail", ""),
            ))

    return QAReport(
        validations=validations,
        edge_cases=edge_cases,
        verdict=qa_data.get("verdict", "PASS"),
        notes=qa_data.get("notes", ""),
    )
