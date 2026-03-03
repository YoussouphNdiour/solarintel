"""
SolarIntel FastAPI backend — pvlib simulation + economic analysis.

pvlib imports are lazy: if pvlib/numpy/pandas have version issues,
the API still starts and uses a fallback estimation (1650 kWh/kWc).
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Root directory of the project (one level above solarintel/ package)
_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger("solarintel.api")

# ---------------------------------------------------------------------------
# Lazy pvlib imports — set to None if unavailable
# ---------------------------------------------------------------------------
_pvlib_ok = False
try:
    from pvlib.location import Location
    from pvlib.pvsystem import PVSystem
    from pvlib.modelchain import ModelChain
    from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
    from pvlib.iotools import get_pvgis_tmy

    _pvlib_ok = True
    logger.info("pvlib loaded successfully")
except Exception as exc:
    logger.warning("pvlib unavailable (%s) — using fallback estimation", exc)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="SolarIntel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from solarintel.api_senelec import router as senelec_router
from solarintel.api_report import router as report_router

app.include_router(senelec_router)
app.include_router(report_router)

# ---------------------------------------------------------------------------
# Frontend static files — serve index.html + assets/
# ---------------------------------------------------------------------------

# Serve the assets/ folder under /assets (images, etc.)
_assets_dir = _ROOT / "assets"
if _assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Return a 204 No Content for favicon requests (no file present)."""
    return Response(status_code=204)


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """Serve the SolarIntel single-page frontend."""
    return FileResponse(str(_ROOT / "index.html"))


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Alias for /health — used as the Render health-check path."""
    return {"status": "ok", "pvlib": _pvlib_ok}


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class SimulateRequest(BaseModel):
    latitude: float = 14.6928
    longitude: float = -17.4467
    panel_count: int = 10
    panel_power_wc: float = 545
    electricity_price_kwh: float = 118
    annual_increase_pct: float = 3.5
    cost_per_wc_xof: float = 650
    system_lifetime_years: int = 25
    degradation_pct_year: float = 0.5
    panel_brand: str = "JA Solar"
    panel_model: str = "JAM72S30-545/MR"
    temp_coeff_pmax: float = -0.350
    # Senelec — grille tarifaire officielle
    senelec_tariff: str | None = None  # DPP, DMP, PPP, PMP ou *_WOYOFAL
    annual_consumption_kwh: float | None = None  # pour calcul tranches


class SimulateResponse(BaseModel):
    simulation: dict
    economics: dict
    system: dict


# ---------------------------------------------------------------------------
# TMY cache (avoid re-fetching for same coordinates)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=32)
def _fetch_tmy(lat: float, lon: float):
    """Fetch PVGIS TMY data with caching."""
    tmy_data, _, _, _ = get_pvgis_tmy(
        latitude=lat,
        longitude=lon,
        outputformat="json",
        usehorizon=True,
        startyear=2005,
        endyear=2020,
    )
    return tmy_data


# ---------------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------------
LOSSES = {
    "soiling": 0.02,
    "mismatch": 0.02,
    "wiring_dc": 0.02,
    "wiring_ac": 0.01,
    "availability": 0.03,
}


def _total_loss_factor() -> float:
    factor = 1.0
    for loss in LOSSES.values():
        factor *= (1 - loss)
    return factor


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "pvlib": _pvlib_ok}


@app.post("/api/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    if not _pvlib_ok:
        return _fallback_response(req)

    # --- Step 1: Location ---
    site = Location(
        latitude=req.latitude,
        longitude=req.longitude,
        altitude=22,
        tz="Africa/Dakar",
        name="Site",
    )

    # --- Step 2: TMY data ---
    try:
        tmy_data = _fetch_tmy(round(req.latitude, 2), round(req.longitude, 2))
    except Exception as exc:
        logger.warning("PVGIS fetch failed (%s), using fallback estimation", exc)
        return _fallback_response(req)

    # --- Step 3: PV System ---
    temp_params = TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

    system = PVSystem(
        surface_tilt=req.latitude,
        surface_azimuth=180,
        module_parameters={
            "pdc0": req.panel_power_wc,
            "gamma_pdc": req.temp_coeff_pmax / 100,
            "b": 0.05,
        },
        inverter_parameters={
            "pdc0": req.panel_power_wc * 1.1,
            "eta_inv_nom": 0.96,
        },
        temperature_model_parameters=temp_params,
        modules_per_string=req.panel_count,
        strings_per_inverter=1,
    )

    # --- Step 4: ModelChain ---
    mc = ModelChain(
        system=system,
        location=site,
        aoi_model="physical",
        spectral_model="no_loss",
    )
    mc.run_model(tmy_data)

    annual_ac_wh = float(mc.results.ac.sum())
    annual_ac_kwh_raw = annual_ac_wh / 1000.0

    # --- Step 5: Apply losses ---
    loss_factor = _total_loss_factor()
    net_annual_kwh = annual_ac_kwh_raw * loss_factor

    # Monthly production
    monthly_ac = mc.results.ac.resample("ME").sum() / 1000.0 * loss_factor
    monthly_production = [round(float(v), 1) for v in monthly_ac.values]
    if len(monthly_production) < 12:
        monthly_production += [0.0] * (12 - len(monthly_production))

    peak_power_kwc = req.panel_count * req.panel_power_wc / 1000.0
    specific_yield = net_annual_kwh / peak_power_kwc if peak_power_kwc > 0 else 0
    capacity_factor = (net_annual_kwh / (peak_power_kwc * 8760) * 100) if peak_power_kwc > 0 else 0
    performance_ratio = specific_yield / 1800 if specific_yield > 0 else 0

    # --- Step 6: Economic analysis ---
    economics = _compute_economics(
        net_annual_kwh=net_annual_kwh,
        peak_power_kwc=peak_power_kwc,
        panel_count=req.panel_count,
        panel_power_wc=req.panel_power_wc,
        electricity_price=req.electricity_price_kwh,
        annual_increase=req.annual_increase_pct / 100,
        cost_per_wc=req.cost_per_wc_xof,
        lifetime=req.system_lifetime_years,
        degradation=req.degradation_pct_year / 100,
        senelec_tariff=req.senelec_tariff,
        annual_consumption_kwh=req.annual_consumption_kwh,
    )

    return SimulateResponse(
        simulation={
            "annual_production_kwh": round(net_annual_kwh, 1),
            "specific_yield_kwh_kwc": round(specific_yield, 1),
            "performance_ratio": round(performance_ratio, 3),
            "capacity_factor_pct": round(capacity_factor, 1),
            "monthly_production_kwh": monthly_production,
            "losses_breakdown": {k: round(v * 100, 1) for k, v in LOSSES.items()},
        },
        economics=economics,
        system={
            "panel_count": req.panel_count,
            "peak_power_kwc": round(peak_power_kwc, 2),
            "panel_brand": req.panel_brand,
            "panel_model": req.panel_model,
            "tilt_deg": round(req.latitude, 1),
            "azimuth_deg": 180,
            "location": {
                "lat": req.latitude,
                "lon": req.longitude,
                "name": "Site",
            },
        },
    )


# ---------------------------------------------------------------------------
# Economic computation (pure Python, Senelec-aware)
# ---------------------------------------------------------------------------
def _compute_economics(
    net_annual_kwh: float,
    peak_power_kwc: float,
    panel_count: int,
    panel_power_wc: float,
    electricity_price: float,
    annual_increase: float,
    cost_per_wc: float,
    lifetime: int,
    degradation: float,
    senelec_tariff: str | None = None,
    annual_consumption_kwh: float | None = None,
) -> dict:
    total_cost = panel_count * panel_power_wc * cost_per_wc

    # Prix effectif : Senelec tranches ou tarif fixe
    if senelec_tariff and annual_consumption_kwh and annual_consumption_kwh > 0:
        from solarintel.config.senelec import (
            get_tariff_effective_price,
            compute_annual_savings_senelec,
        )
        use_woyofal = "WOYOFAL" in (senelec_tariff or "").upper()
        tariff_code = (senelec_tariff or "DPP").replace("_WOYOFAL", "")
        monthly_kwh = annual_consumption_kwh / 12
        senelec_savings = compute_annual_savings_senelec(
            net_annual_kwh, annual_consumption_kwh,
            tariff_code=tariff_code, use_woyofal=use_woyofal,
        )
        annual_savings_base = senelec_savings["annual_savings_xof"]
        # Prix effectif équivalent pour le cashflow (savings ≈ prod × prix_eff)
        electricity_price = (
            annual_savings_base / net_annual_kwh
            if net_annual_kwh > 0
            else get_tariff_effective_price(monthly_kwh, tariff_code, use_woyofal)
        )
        senelec_detail = {
            "tariff": senelec_tariff,
            "tarif_effectif_xof_kwh": senelec_savings["tarif_effectif_xof_kwh"],
            "monthly_bill_before_xof": senelec_savings["monthly_bill_before_xof"],
            "monthly_bill_after_xof": senelec_savings["monthly_bill_after_xof"],
        }
    else:
        annual_savings_base = net_annual_kwh * electricity_price
        senelec_detail = None

    cashflow = []
    cumulative = -total_cost
    payback_year = float(lifetime)
    total_production = 0.0
    total_savings = 0.0
    payback_found = False

    for year in range(1, lifetime + 1):
        prod_year = net_annual_kwh * ((1 - degradation) ** year)
        price_year = electricity_price * ((1 + annual_increase) ** year)
        savings_year = prod_year * price_year
        cumulative += savings_year
        total_production += prod_year
        total_savings += savings_year
        cashflow.append(round(cumulative))

        if cumulative >= 0 and not payback_found:
            if savings_year > 0:
                fraction = (0 - (cumulative - savings_year)) / savings_year
                payback_year = year - 1 + fraction
            payback_found = True

    lcoe = total_cost / total_production if total_production > 0 else 0
    roi = ((total_savings - total_cost) / total_cost * 100) if total_cost > 0 else 0
    annual_savings_y1 = annual_savings_base * (1 + annual_increase)

    result = {
        "total_cost_xof": round(total_cost),
        "annual_savings_year1_xof": round(annual_savings_y1),
        "payback_years": round(payback_year, 1),
        "lcoe_xof_kwh": round(lcoe, 1),
        "roi_pct": round(roi, 1),
        "npv_25y_xof": round(cumulative),
        "cashflow_annual": cashflow,
    }
    if senelec_detail:
        result["senelec"] = senelec_detail
    return result


# ---------------------------------------------------------------------------
# Fallback (no pvlib / PVGIS unavailable) — 1650 kWh/kWc for West Africa
# ---------------------------------------------------------------------------
def _fallback_response(req: SimulateRequest) -> SimulateResponse:
    peak_power_kwc = req.panel_count * req.panel_power_wc / 1000.0
    net_annual_kwh = peak_power_kwc * 1650 * _total_loss_factor()

    economics = _compute_economics(
        net_annual_kwh=net_annual_kwh,
        peak_power_kwc=peak_power_kwc,
        panel_count=req.panel_count,
        panel_power_wc=req.panel_power_wc,
        electricity_price=req.electricity_price_kwh,
        annual_increase=req.annual_increase_pct / 100,
        cost_per_wc=req.cost_per_wc_xof,
        lifetime=req.system_lifetime_years,
        degradation=req.degradation_pct_year / 100,
        senelec_tariff=req.senelec_tariff,
        annual_consumption_kwh=req.annual_consumption_kwh,
    )

    monthly = [round(net_annual_kwh / 12, 1)] * 12

    return SimulateResponse(
        simulation={
            "annual_production_kwh": round(net_annual_kwh, 1),
            "specific_yield_kwh_kwc": round(net_annual_kwh / peak_power_kwc, 1) if peak_power_kwc > 0 else 0,
            "performance_ratio": 0.78,
            "capacity_factor_pct": round(net_annual_kwh / (peak_power_kwc * 8760) * 100, 1) if peak_power_kwc > 0 else 0,
            "monthly_production_kwh": monthly,
            "losses_breakdown": {k: round(v * 100, 1) for k, v in LOSSES.items()},
        },
        economics=economics,
        system={
            "panel_count": req.panel_count,
            "peak_power_kwc": round(peak_power_kwc, 2),
            "panel_brand": req.panel_brand,
            "panel_model": req.panel_model,
            "tilt_deg": round(req.latitude, 1),
            "azimuth_deg": 180,
            "location": {
                "lat": req.latitude,
                "lon": req.longitude,
                "name": "Site (estimation)",
            },
        },
    )
