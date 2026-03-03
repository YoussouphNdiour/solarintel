"""
Endpoints Senelec — facture et économies.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from solarintel.config.senelec import (
    compute_bill_tranches,
    compute_annual_savings_senelec,
    SENELEC_TARIFF_CODES,
)

router = APIRouter(prefix="/api/senelec", tags=["senelec"])


@router.get("/tariffs")
def get_tariffs():
    """Retourne les grilles tarifaires Senelec officielles."""
    from solarintel.config.senelec import (
        SENELEC_TRANCHES,
        SENELEC_WOYOFAL,
        SENELEC_GRANDE_PUISSANCE,
    )
    return {
        "tranches": {
            k: {"t1": v[0], "t2": v[1], "t3": v[2]}
            for k, v in {**SENELEC_TRANCHES, **SENELEC_WOYOFAL}.items()
        },
        "grande_puissance": SENELEC_GRANDE_PUISSANCE,
        "codes": SENELEC_TARIFF_CODES,
    }


class BillRequest(BaseModel):
    monthly_kwh: float
    tariff_code: str = "DPP"
    use_woyofal: bool = False


class SavingsRequest(BaseModel):
    annual_production_kwh: float
    annual_consumption_kwh: float
    tariff_code: str = "DPP"
    use_woyofal: bool = False


@router.post("/bill")
def compute_bill(req: BillRequest):
    """Calcule la facture mensuelle Senelec selon les tranches."""
    use_woyofal = req.use_woyofal or "WOYOFAL" in (req.tariff_code or "").upper()
    code = (req.tariff_code or "DPP").replace("_WOYOFAL", "")
    return compute_bill_tranches(req.monthly_kwh, code, use_woyofal)


@router.post("/savings")
def compute_savings(req: SavingsRequest):
    """Estime les économies annuelles PV vs réseau Senelec."""
    use_woyofal = req.use_woyofal or "WOYOFAL" in (req.tariff_code or "").upper()
    code = (req.tariff_code or "DPP").replace("_WOYOFAL", "")
    return compute_annual_savings_senelec(
        req.annual_production_kwh,
        req.annual_consumption_kwh,
        tariff_code=code,
        use_woyofal=use_woyofal,
    )
