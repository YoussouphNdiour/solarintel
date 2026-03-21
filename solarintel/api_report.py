"""
SolarIntel — POST /api/report

Génère un rapport PDF à partir des données de simulation et des équipements.
Tente d'appeler CrewAI/Ollama pour les recommandations IA ; si indisponible,
utilise des recommandations statiques basées sur les KPIs.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger("solarintel.api_report")

# ---------------------------------------------------------------------------
# Ollama configuration — override via environment variables on Render.com
# ---------------------------------------------------------------------------
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

logger.info("Ollama config — host=%s model=%s", OLLAMA_HOST, OLLAMA_MODEL)

router = APIRouter()


# ---------------------------------------------------------------------------
# Ollama status endpoint — called by the frontend to show connection state
# ---------------------------------------------------------------------------

@router.get("/api/ollama/status")
def ollama_status():
    """Vérifie si le serveur Ollama est joignable et liste les modèles disponibles."""
    import urllib.request
    import json as _json

    try:
        url = OLLAMA_HOST.rstrip("/") + "/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = _json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        return {
            "status": "online",
            "host": OLLAMA_HOST,
            "active_model": OLLAMA_MODEL,
            "available_models": models,
        }
    except Exception as exc:
        return {
            "status": "offline",
            "host": OLLAMA_HOST,
            "active_model": OLLAMA_MODEL,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class ApplianceItem(BaseModel):
    name: str = "Appareil"
    qty: int = 1
    power: float = 100       # watts
    hoursDay: float = 0
    hoursNight: float = 0
    cos_phi: float = 1.0     # facteur de puissance (0.1–1.0)


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
    daily_kwh_total: float = 0
    daily_kwh_day: float = 0
    daily_kwh_night: float = 0
    peak_night_w: float = 0
    # Prix équipements réels (envoyés par le frontend)
    panel_price_xof_wc: float = 0       # XOF/Wc (converti depuis prix/panneau)
    capex_panels_xof: float = 0
    capex_total_xof: float = 0
    install_pct: float = 15
    install_type: str = "autoconsommation"
    # Métadonnées rapport
    company_name: str = "SolarIntel"
    report_title: str = "Étude de dimensionnement PV"
    client_name: str = ""
    # Personnalisation visuelle
    logo_b64: str = ""            # logo encodé en base64 (data URL ou raw base64)
    color_primary: str = "#0EA5E9"
    color_secondary: str = "#0369A1"
    # KPIs pré-calculés par le frontend / l'API simulate
    kpi_production_kwh: float = 0
    kpi_coverage_pct: float = 0
    kpi_savings_xof: float = 0
    kpi_payback_years: float = 0
    kpi_lcoe: float = 0
    kpi_peak_power_kwc: float = 0
    # Facteur de puissance
    site_pf_avg: float = 1.0               # FP moyen pondéré du site
    peak_apparent_power_kva: float = 0     # puissance apparente totale (kVA)
    inverter_power_kva: float = 0          # capacité nominale onduleur (kVA)


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

def _fmt(value: float) -> str:
    return f"{value:,.0f}".replace(",", "\u202f")


def _build_cashflow(capex: float, annual_savings: float, years: int = 25) -> list[float]:
    """Flux de trésorerie cumulé simplifié sur N ans."""
    if capex <= 0 or annual_savings <= 0:
        return [0.0] * years
    cf = [-capex]
    for y in range(1, years):
        cf.append(cf[-1] + annual_savings * (1.035 ** y))   # +3.5% hausse tarif
    return [round(v) for v in cf]


def _estimate_monthly_kwh(annual_kwh: float) -> list[float]:
    """Distribue la production annuelle sur 12 mois (Dakar, poids solaires)."""
    # Poids mensuels basés sur l'irradiation horizontale à Dakar (PVGIS TMY normalisé)
    weights = [8.8, 8.0, 8.6, 8.4, 8.7, 8.1, 7.6, 7.3, 7.6, 8.4, 8.7, 8.8]
    total_w = sum(weights)
    return [round(annual_kwh * w / total_w, 1) for w in weights]


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

    # ── CAPEX — utiliser les prix réels envoyés par le frontend ─────────────
    capex_panels   = req.capex_panels_xof if req.capex_panels_xof > 0 else (
                         req.panel_count * req.panel_power_wc * (req.panel_price_xof_wc or 650)
                     )
    capex_inverter = req.inverter_qty * req.inverter_price_xof
    capex_battery  = (req.battery_qty * req.battery_price_xof if req.battery_model else 0)
    capex_equip    = capex_panels + capex_inverter + capex_battery
    capex_install  = capex_equip * (req.install_pct / 100)
    total_capex    = req.capex_total_xof if req.capex_total_xof > 0 else (capex_equip + capex_install)

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
        QAValidation(
            code="V7", label="Facteur de puissance site ≥ 0,80",
            status="PASS" if req.site_pf_avg >= 0.80 else "WARNING",
            detail=f"FP = {req.site_pf_avg:.2f}  →  S_req = {req.peak_apparent_power_kva:.1f} kVA",
        ),
        QAValidation(
            code="V8", label="Capacité onduleur (kVA) ≥ charge apparente",
            status=(
                "PASS" if req.inverter_power_kva >= req.peak_apparent_power_kva > 0
                else "INFO" if req.peak_apparent_power_kva == 0
                else "WARNING"
            ),
            detail=(
                f"Onduleur {req.inverter_power_kva:.1f} kVA vs charge {req.peak_apparent_power_kva:.1f} kVA"
                if req.inverter_power_kva > 0
                else "Onduleur non renseigné"
            ),
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
            monthly_production_kwh=_estimate_monthly_kwh(req.kpi_production_kwh),
            specific_yield_kwh_kwc=(
                round(req.kpi_production_kwh / peak_kwc, 1) if peak_kwc > 0 else 0
            ),
            performance_ratio=0.78,
            total_losses_pct=9.6,
        ),
        economics=EconomicAnalysis(
            total_cost_xof=round(total_capex),
            cost_per_kwc_xof=round(total_capex / peak_kwc) if peak_kwc > 0 else 0,
            lcoe_xof_kwh=round(req.kpi_lcoe, 1),
            roi_pct=round(
                (req.kpi_savings_xof * 25 - total_capex) / total_capex * 100, 1
            ) if total_capex > 0 else 0,
            payback_years=round(req.kpi_payback_years, 1),
            annual_savings_xof=round(req.kpi_savings_xof),
            npv_xof=round(req.kpi_savings_xof * 25 - total_capex) if total_capex > 0 else 0,
            cashflow_cumulative=_build_cashflow(total_capex, req.kpi_savings_xof),
        ),
        qa=QAReport(validations=qa_checks, verdict="PASS"),
        raw_crew_output=(
            "=== LISTE MATÉRIEL ===\n" + "\n".join(equipment_lines) +
            "\n\n=== RECOMMANDATIONS IA ===\n" + ai_recs
        ),
    )

    # Champs supplémentaires (non dans SolarReport de base) — attachés dynamiquement
    report.client_name = req.client_name
    report.appliances  = [a.model_dump() for a in req.appliances] if req.appliances else []
    report.equipment   = {
        "inverter": {
            "Marque":          req.inverter_brand,
            "Modèle":          req.inverter_model or "—",
            "Quantité":        f"{req.inverter_qty}",
            "Puissance (kVA)": f"{req.inverter_power_kva:.1f} kVA" if req.inverter_power_kva > 0 else "—",
            "Charge apparente":f"{req.peak_apparent_power_kva:.1f} kVA (site)",
            "FP moyen site":   f"{req.site_pf_avg:.2f}",
            "Prix unit.":      f"{_fmt(req.inverter_price_xof)} XOF",
            "Total":           f"{_fmt(capex_inverter)} XOF",
        } if req.inverter_model else {},
        "battery": {
            "Modèle":    req.battery_model,
            "Quantité":  f"{req.battery_qty}",
            "Prix unit.":f"{_fmt(req.battery_price_xof)} XOF",
            "Total":     f"{_fmt(capex_battery)} XOF",
        } if req.battery_model else {},
        "capex": {
            "Panneaux solaires":        capex_panels,
            "Onduleur(s)":              capex_inverter,
            "Batterie(s)":              capex_battery,
            f"Instal./Livr./Maint. ({req.install_pct:.0f}%)": capex_install,
            "CAPEX Total":              total_capex,
        },
    }

    # ── Logo — priorité : logo uploadé par l'utilisateur, sinon assets/ ────────
    _here = os.path.dirname(os.path.abspath(__file__))
    logo_path: str | None = None
    _user_logo_tmp: str | None = None

    if req.logo_b64:
        try:
            import base64
            raw = req.logo_b64
            # Supprimer le préfixe data URL si présent (data:image/png;base64,...)
            if "," in raw:
                raw = raw.split(",", 1)[1]
            logo_bytes = base64.b64decode(raw)
            tmp_logo_fd, _user_logo_tmp = tempfile.mkstemp(suffix=".png")
            os.write(tmp_logo_fd, logo_bytes)
            os.close(tmp_logo_fd)
            logo_path = _user_logo_tmp
        except Exception as exc:
            logger.warning("Impossible de décoder le logo uploadé : %s", exc)

    if not logo_path:
        logo_candidates = [
            os.path.join(_here, "..", "assets", "logo_solarintel.png"),
            os.path.join(_here, "..", "assets", "logo.png"),
        ]
        logo_path = next((p for p in logo_candidates if os.path.isfile(p)), None)

    # ReportGenerator.generate() only accepts a file path, so we use a temp file.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(tmp_fd)
    try:
        gen = ReportGenerator(
            report,
            logo_path=logo_path,
            company_name=req.company_name,
            color_primary=req.color_primary or "#0EA5E9",
            color_secondary=req.color_secondary or "#0369A1",
        )
        gen.generate(output_path=tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        if _user_logo_tmp:
            try:
                os.unlink(_user_logo_tmp)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# CrewAI / Ollama (lightweight, timeout-safe)
# ---------------------------------------------------------------------------

def _run_crewai(req: ReportRequest) -> str | None:
    """Try a single-agent CrewAI analysis. Returns None if unavailable."""
    try:
        from crewai import Agent, Task, Crew, Process  # type: ignore
        from langchain_ollama import OllamaLLM          # type: ignore

        llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_HOST, timeout=90)

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
