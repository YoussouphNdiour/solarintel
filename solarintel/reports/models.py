"""
Modèles Pydantic pour le rapport PDF SolarIntel.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from solarintel.config.constants import (
    DEFAULT_LOCATION,
    DEFAULT_PANEL,
    ECONOMIC_DEFAULTS,
)


# ---------------------------------------------------------------------------
# Configuration système
# ---------------------------------------------------------------------------
class SystemConfig(BaseModel):
    """Spécifications du système PV."""

    panel_brand: str = DEFAULT_PANEL["brand"]
    panel_model: str = DEFAULT_PANEL["model"]
    panel_power_wc: int = DEFAULT_PANEL["power_wc"]
    panel_efficiency: float = DEFAULT_PANEL["efficiency"]
    panel_count: int = 1
    total_power_kwc: float = 0.0

    location_name: str = DEFAULT_LOCATION["name"]
    latitude: float = DEFAULT_LOCATION["latitude"]
    longitude: float = DEFAULT_LOCATION["longitude"]
    altitude: float = DEFAULT_LOCATION["altitude"]

    orientation_azimuth: float = 180.0  # plein sud
    tilt: float = 15.0  # inclinaison (°)


# ---------------------------------------------------------------------------
# Résultats de simulation pvlib
# ---------------------------------------------------------------------------
class SimulationResults(BaseModel):
    """Résultats de la simulation photovoltaïque."""

    annual_production_kwh: float = 0.0
    monthly_production_kwh: list[float] = Field(
        default_factory=lambda: [0.0] * 12,
    )
    specific_yield_kwh_kwc: float = 0.0
    performance_ratio: float = 0.0

    # Pertes (%)
    soiling_loss_pct: float = 2.0
    mismatch_loss_pct: float = 1.0
    wiring_loss_pct: float = 1.5
    availability_loss_pct: float = 1.0
    temperature_loss_pct: float = 3.0
    total_losses_pct: float = 0.0


# ---------------------------------------------------------------------------
# Analyse économique
# ---------------------------------------------------------------------------
class EconomicAnalysis(BaseModel):
    """Résultats de l'analyse économique."""

    total_cost_xof: float = 0.0
    cost_per_kwc_xof: float = ECONOMIC_DEFAULTS["cost_per_wc_xof"] * 1000
    lcoe_xof_kwh: float = 0.0
    roi_pct: float = 0.0
    payback_years: float = 0.0
    npv_xof: float = 0.0
    annual_savings_xof: float = 0.0
    cashflow_cumulative: list[float] = Field(
        default_factory=lambda: [0.0] * 25,
    )
    currency: str = ECONOMIC_DEFAULTS["currency"]


# ---------------------------------------------------------------------------
# Rapport QA
# ---------------------------------------------------------------------------
class QAValidation(BaseModel):
    """Un point de la matrice de validation."""

    code: str  # V1, V2, ..., EC1, EC2, ...
    label: str
    status: str = "PASS"  # PASS | FAIL | WARNING
    detail: str = ""


class QAReport(BaseModel):
    """Rapport complet d'assurance qualité."""

    validations: list[QAValidation] = Field(default_factory=list)
    edge_cases: list[QAValidation] = Field(default_factory=list)
    verdict: str = "PASS"
    notes: str = ""


# ---------------------------------------------------------------------------
# Rapport racine
# ---------------------------------------------------------------------------
class SolarReport(BaseModel):
    """Modèle racine du rapport PDF SolarIntel."""

    model_config = ConfigDict(extra="allow")

    # Métadonnées
    project_name: str = "Projet Solaire"
    company_name: str = "SolarIntel"
    report_title: str = "Rapport de Dimensionnement Solaire"
    generation_date: date = Field(default_factory=date.today)
    executive_summary: str = ""

    # Sections
    system: SystemConfig = Field(default_factory=SystemConfig)
    simulation: SimulationResults = Field(default_factory=SimulationResults)
    economics: EconomicAnalysis = Field(default_factory=EconomicAnalysis)
    qa: QAReport = Field(default_factory=QAReport)

    # Texte brut CrewAI (fallback)
    raw_crew_output: Optional[str] = None
