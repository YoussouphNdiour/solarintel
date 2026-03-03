"""
SolarIntel — POST /api/report

Génère un rapport PDF à partir des données de simulation et des équipements.
Tente d'appeler CrewAI/Ollama pour les recommandations IA ; si indisponible,
utilise des recommandations statiques basées sur les KPIs.
"""

from __future__ import annotations

import io
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger("solarintel.api_report")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class ApplianceItem(BaseModel):
    name: str = "Appareil"
    qty: int = 1
    power: float = 100       # watts
    hoursDay: float = 0
    hoursNight: float = 0


class ReportRequest(BaseModel):
    # Localisation
    latitude: float = 14.6928
    longitude: float = -17.4467
    # Panneaux
    panel_count: int = 0
    panel_power_wc: float = 545
    panel_brand: str = "JA Solar"
    panel_model: str = ""
    temp_coeff_pmax: float = -0.35
    # Économie
    electricity_price_kwh: float = 118
    annual_increase_pct: float = 3.5
    senelec_tariff: Optional[str] = None
    annual_consumption_kwh: Optional[float] = None
    # Onduleur
    inverter_brand: str = "GOODWE"
    inverter_model: str = ""
    inverter_qty: int = 1
    inverter_price_xof: float = 450000
    # Batterie
    battery_model: str = ""
    battery_qty: int = 0
    battery_price_xof: float = 0
    # Bilan énergétique
    appliances: list[ApplianceItem] = []
    # Métadonnées rapport
    company_name: str = "SolarIntel"
    report_title: str = "Étude de dimensionnement PV"
    client_name: str = ""
    # KPIs pré-calculés par le frontend / l'API simulate
    kpi_production_kwh: float = 0
    kpi_coverage_pct: float = 0
    kpi_savings_xof: float = 0
    kpi_payback_years: float = 0
    kpi_lcoe: float = 0


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/api/report")
async def generate_report(req: ReportRequest):
    """
    Génère et retourne un rapport PDF SolarIntel au format binaire.
    """
    pdf_bytes = _build_pdf(req)
    filename  = f"rapport_solarintel_{date.today()}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def _build_pdf(req: ReportRequest) -> bytes:
    try:
        from solarintel.reports.generator import ReportGenerator
        from solarintel.reports.models import (
            SolarReport,
            SystemConfig,
            SimulationResults,
            EconomicAnalysis,
            QAReport,
            QAValidation,
        )
    except ImportError as exc:
        logger.error("Report generator unavailable: %s", exc)
        return _plain_text_fallback(req)

    peak_kwc = req.panel_count * req.panel_power_wc / 1000.0

    # ── CAPEX breakdown ──────────────────────────────────────────────────────
    capex_panels   = req.panel_count * req.panel_power_wc * 650  # 650 XOF/Wc
    capex_inverter = req.inverter_qty * req.inverter_price_xof
    capex_battery  = (req.battery_qty * req.battery_price_xof
                      if req.battery_model else 0)
    total_capex    = capex_panels + capex_inverter + capex_battery

    # ── Equipment list (for report table) ───────────────────────────────────
    equipment_lines: list[str] = []
    if req.panel_count > 0:
        equipment_lines.append(
            f"Panneaux {req.panel_brand} {req.panel_model} "
            f"×{req.panel_count} "
            f"({int(req.panel_power_wc)} Wc) "
            f"= {_fmt(capex_panels)} XOF"
        )
    if req.inverter_model:
        equipment_lines.append(
            f"Onduleur {req.inverter_brand} {req.inverter_model} "
            f"×{req.inverter_qty} "
            f"= {_fmt(capex_inverter)} XOF"
        )
    if req.battery_model and req.battery_qty > 0:
        equipment_lines.append(
            f"Batterie {req.battery_model} "
            f"×{req.battery_qty} "
            f"= {_fmt(capex_battery)} XOF"
        )
    equipment_lines.append(f"CAPEX Total : {_fmt(total_capex)} XOF")

    # ── Appliance summary ────────────────────────────────────────────────────
    appliance_lines: list[str] = []
    for a in req.appliances:
        kwh = a.qty * a.power * (a.hoursDay + a.hoursNight) / 1000
        appliance_lines.append(
            f"• {a.name} ×{a.qty}  {int(a.power)} W  "
            f"{a.hoursDay}h/j + {a.hoursNight}h/n  →  {kwh:.2f} kWh/j"
        )

    # ── AI recommendations ───────────────────────────────────────────────────
    ai_recs = _run_crewai(req) or _static_recommendations(req)

    # ── Executive summary ────────────────────────────────────────────────────
    exec_summary = (
        f"Projet : {req.report_title}\n"
        f"Client : {req.client_name or '—'}\n"
        f"Site   : {req.latitude:.4f}°N, {req.longitude:.4f}°E\n\n"
        f"Système {peak_kwc:.2f} kWc — {req.panel_count} panneaux "
        f"{req.panel_brand} {req.panel_model}.\n"
        f"Production annuelle estimée : {_fmt(req.kpi_production_kwh)} kWh/an "
        f"(couverture {req.kpi_coverage_pct:.0f}%).\n"
        f"Économie annuelle (année 1) : {_fmt(req.kpi_savings_xof)} XOF.\n"
        f"Retour sur investissement   : {req.kpi_payback_years:.1f} ans.\n"
        f"CAPEX total estimé          : {_fmt(total_capex)} XOF.\n"
    )

    # ── QA matrix ────────────────────────────────────────────────────────────
    qa_checks = [
        QAValidation(
            code="V1", label="Puissance crête cohérente",
            status="PASS" if peak_kwc > 0 else "FAIL",
            detail=f"{peak_kwc:.2f} kWc installé",
        ),
        QAValidation(
            code="V2", label="Taux de couverture acceptable (50–150%)",
            status="PASS" if 50 <= req.kpi_coverage_pct <= 150 else "WARNING",
            detail=f"{req.kpi_coverage_pct:.0f}%",
        ),
        QAValidation(
            code="V3", label="Retour investissement < 15 ans",
            status="PASS" if 0 < req.kpi_payback_years <= 15 else "WARNING",
            detail=f"{req.kpi_payback_years:.1f} ans",
        ),
        QAValidation(
            code="V4", label="LCOE compétitif vs réseau",
            status="PASS" if 0 < req.kpi_lcoe < 200 else "WARNING",
            detail=f"{req.kpi_lcoe:.1f} XOF/kWh",
        ),
        QAValidation(
            code="V5", label="Onduleur sélectionné",
            status="PASS" if req.inverter_model else "WARNING",
            detail=req.inverter_model or "Non renseigné",
        ),
        QAValidation(
            code="V6", label="Stockage batterie",
            status="PASS" if req.battery_model else "INFO",
            detail=req.battery_model or "Aucun stockage",
        ),
    ]

    # ── Assemble SolarReport ─────────────────────────────────────────────────
    report = SolarReport(
        project_name=req.report_title,
        company_name=req.company_name,
        report_title=req.report_title,
        executive_summary=exec_summary + "\n\nBilan énergétique :\n" + "\n".join(appliance_lines),
        system=SystemConfig(
            panel_brand=req.panel_brand,
            panel_model=req.panel_model,
            panel_power_wc=int(req.panel_power_wc),
            panel_count=req.panel_count,
            total_power_kwc=round(peak_kwc, 2),
            latitude=req.latitude,
            longitude=req.longitude,
            orientation_azimuth=180.0,
            tilt=round(req.latitude, 1),
        ),
        simulation=SimulationResults(
            annual_production_kwh=round(req.kpi_production_kwh, 1),
            specific_yield_kwh_kwc=(
                round(req.kpi_production_kwh / peak_kwc, 1) if peak_kwc > 0 else 0
            ),
            performance_ratio=0.78,
        ),
        economics=EconomicAnalysis(
            total_cost_xof=round(total_capex),
            lcoe_xof_kwh=round(req.kpi_lcoe, 1),
            roi_pct=round(
                (req.kpi_savings_xof * 25 - total_capex) / total_capex * 100, 1
            ) if total_capex > 0 else 0,
            payback_years=round(req.kpi_payback_years, 1),
            annual_savings_xof=round(req.kpi_savings_xof),
        ),
        qa=QAReport(validations=qa_checks, verdict="PASS"),
        raw_crew_output=(
            "=== LISTE MATÉRIEL ===\n" + "\n".join(equipment_lines) +
            "\n\n=== RECOMMANDATIONS IA ===\n" + ai_recs
        ),
    )

    buf = io.BytesIO()
    gen = ReportGenerator(report)
    gen.generate(output=buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# CrewAI / Ollama (lightweight, timeout-safe)
# ---------------------------------------------------------------------------

def _run_crewai(req: ReportRequest) -> str | None:
    """Try a single-agent CrewAI analysis. Returns None if unavailable."""
    try:
        from crewai import Agent, Task, Crew, Process  # type: ignore
        from langchain_ollama import OllamaLLM          # type: ignore

        llm = OllamaLLM(model="llama3", timeout=60)

        night_kwh = sum(
            a.qty * a.power * a.hoursNight / 1000 for a in req.appliances
        )
        bat_kwh = 0.0
        if req.battery_model:
            try:
                bat_kwh = float(req.battery_model.split()[1].replace("kWh", ""))
            except (IndexError, ValueError):
                pass

        context = (
            f"Projet : {req.report_title}\n"
            f"Client : {req.client_name or '—'}\n"
            f"Site   : {req.latitude:.4f}°N, {req.longitude:.4f}°E\n"
            f"Système: {req.panel_count}×{req.panel_brand} {req.panel_model} "
            f"({req.panel_count * req.panel_power_wc / 1000:.1f} kWc)\n"
            f"Onduleur: {req.inverter_brand} {req.inverter_model} ×{req.inverter_qty}\n"
            f"Batterie: {req.battery_model or 'Aucune'} ×{req.battery_qty}\n"
            f"Production annuelle: {req.kpi_production_kwh:.0f} kWh/an\n"
            f"Consommation annuelle: {req.annual_consumption_kwh or '?'} kWh/an\n"
            f"Taux couverture: {req.kpi_coverage_pct:.0f}%\n"
            f"Charge nocturne: {night_kwh:.1f} kWh/nuit\n"
            f"Stockage disponible: {bat_kwh:.1f} kWh\n"
            f"CAPEX total: {req.panel_count * req.panel_power_wc * 650 + req.inverter_qty * req.inverter_price_xof:,.0f} XOF\n"
            f"ROI: {req.kpi_payback_years:.1f} ans\n"
        )

        analyst = Agent(
            role="Expert en Énergie Solaire PV — Afrique de l'Ouest",
            goal="Analyser le dimensionnement PV et formuler des recommandations techniques en français",
            backstory=(
                "Ingénieur solaire senior avec 15 ans d'expérience en dimensionnement PV "
                "en Afrique de l'Ouest. Expert pvlib, onduleurs, et systèmes de stockage."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        task = Task(
            description=(
                f"Analysez ce projet solaire PV et rédigez des recommandations techniques "
                f"professionnelles en français (250 mots maximum, structurées en 3 points) :\n\n{context}"
            ),
            agent=analyst,
            expected_output=(
                "Recommandations techniques structurées en français : "
                "1) Analyse du dimensionnement, 2) Risques/alertes, 3) Optimisations suggérées."
            ),
        )

        crew   = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()
        return str(result) if result else None

    except Exception as exc:
        logger.warning("CrewAI/Ollama unavailable (%s) — using static recommendations", exc)
        return None


# ---------------------------------------------------------------------------
# Static recommendations (fallback)
# ---------------------------------------------------------------------------

def _static_recommendations(req: ReportRequest) -> str:
    peak_kwc    = req.panel_count * req.panel_power_wc / 1000
    coverage    = req.kpi_coverage_pct
    night_kwh   = sum(a.qty * a.power * a.hoursNight / 1000 for a in req.appliances)

    bat_kwh = 0.0
    if req.battery_model:
        try:
            bat_kwh = float(req.battery_model.split()[1].replace("kWh", ""))
        except (IndexError, ValueError):
            pass
    bat_total = bat_kwh * req.battery_qty

    lines: list[str] = []

    # 1. Dimensionnement
    if coverage < 60:
        lines.append(
            f"⚠ Taux de couverture insuffisant ({coverage:.0f}%). "
            f"Augmentez la puissance installée vers {peak_kwc * 1.5:.1f} kWc "
            "pour couvrir au moins 80% de la consommation."
        )
    elif coverage > 130:
        lines.append(
            f"ℹ Surproduction estimée ({coverage:.0f}%). "
            "Envisagez un système de stockage supplémentaire ou une injection réseau "
            "pour valoriser l'excédent de production."
        )
    else:
        lines.append(
            f"✓ Taux de couverture optimal ({coverage:.0f}%). "
            f"Le système de {peak_kwc:.2f} kWc est bien dimensionné "
            "par rapport à la consommation déclarée."
        )

    # 2. Stockage vs charge nocturne
    if night_kwh > 0 and bat_total == 0:
        lines.append(
            f"⚠ Charge nocturne de {night_kwh:.1f} kWh détectée sans stockage. "
            "Recommandation : au minimum 1 batterie UHOME 10.0 kWh pour couvrir "
            "la consommation nocturne et améliorer l'autonomie."
        )
    elif bat_total > 0 and night_kwh > bat_total * 0.8:
        lines.append(
            f"⚠ Capacité de stockage ({bat_total:.1f} kWh) insuffisante pour couvrir "
            f"la charge nocturne ({night_kwh:.1f} kWh). "
            "Ajoutez un module UHOME supplémentaire."
        )
    elif bat_total > 0:
        lines.append(
            f"✓ Capacité de stockage de {bat_total:.1f} kWh. "
            f"Couverture nocturne estimée : {min(100, bat_total / night_kwh * 100):.0f}%."
            if night_kwh > 0 else
            f"✓ Capacité de stockage de {bat_total:.1f} kWh disponible."
        )

    # 3. Économique & installation
    lines.append(
        f"✓ Économie annuelle estimée : {_fmt(req.kpi_savings_xof)} XOF "
        f"avec un retour sur investissement en {req.kpi_payback_years:.1f} ans. "
        f"Orientation recommandée : Sud (azimut 180°), inclinaison {req.latitude:.1f}° "
        "(égale à la latitude du site). "
        "Maintenance préventive semestrielle conseillée (nettoyage, contrôle des connexions)."
    )

    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _plain_text_fallback(req: ReportRequest) -> bytes:
    """Retourne un texte brut si reportlab est indisponible."""
    peak_kwc   = req.panel_count * req.panel_power_wc / 1000
    total_capex = (
        req.panel_count * req.panel_power_wc * 650
        + req.inverter_qty * req.inverter_price_xof
        + (req.battery_qty * req.battery_price_xof if req.battery_model else 0)
    )
    lines = [
        "SolarIntel — Rapport de Dimensionnement PV",
        "=" * 50,
        f"Date           : {date.today()}",
        f"Client         : {req.client_name or '—'}",
        f"Entreprise     : {req.company_name}",
        "",
        "SYSTÈME",
        f"  Panneaux     : {req.panel_count}× {req.panel_brand} {req.panel_model}",
        f"  Puissance    : {peak_kwc:.2f} kWc",
        f"  Onduleur     : {req.inverter_brand} {req.inverter_model}",
        f"  Batterie     : {req.battery_model or 'Aucune'}",
        "",
        "PRODUCTION",
        f"  Annuelle     : {_fmt(req.kpi_production_kwh)} kWh/an",
        f"  Couverture   : {req.kpi_coverage_pct:.0f}%",
        "",
        "ÉCONOMIE",
        f"  CAPEX        : {_fmt(total_capex)} XOF",
        f"  Économie/an  : {_fmt(req.kpi_savings_xof)} XOF",
        f"  ROI          : {req.kpi_payback_years:.1f} ans",
        f"  LCOE         : {req.kpi_lcoe:.1f} XOF/kWh",
    ]
    return "\n".join(lines).encode("utf-8")
