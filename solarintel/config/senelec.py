"""
Grilles tarifaires Senelec — Sénégal.

Source : Document officiel Senelec "Fourniture d'électricité en Basse tension
et en Moyenne/Haute Tension" — https://www.senelec.sn/grille-tarifaire

Tranches mensuelles : 1ère (0-150 kWh), 2ème (151-250 kWh), 3ème (>250 kWh)
Heures de pointe : 19h-23h | Heures hors pointe : 0h-19h et 23h-24h
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tranches de consommation mensuelle (kWh)
# ---------------------------------------------------------------------------
TRANCHE_1_MAX = 150   # 0 - 150 kWh
TRANCHE_2_MAX = 250   # 151 - 250 kWh
# Tranche 3 : > 250 kWh

# ---------------------------------------------------------------------------
# Basse tension — Tranches (FCFA/kWh)
# ---------------------------------------------------------------------------
SENELEC_TRANCHES: dict[str, tuple[float, float, float]] = {
    # Usage Domestique
    "DPP": (91.17, 136.49, 159.36),   # Domestique Petite Puissance
    "DMP": (111.23, 143.54, 158.46),  # Domestique Moyenne Puissance
    # Usage Professionnel
    "PPP": (163.81, 189.84, 208.63),  # Professionnel Petite Puissance
    "PMP": (165.01, 191.01, 210.81),  # Professionnel Moyenne Puissance
}

# Prépaiement (WOYOFAL) : tranche 3 valorisée au tarif tranche 2
SENELEC_WOYOFAL: dict[str, tuple[float, float, float]] = {
    "DPP_WOYOFAL": (91.17, 136.49, 136.49),
    "DMP_WOYOFAL": (111.23, 143.54, 143.54),
    "PPP_WOYOFAL": (163.81, 189.84, 189.84),
    "PMP_WOYOFAL": (165.01, 191.01, 191.01),
}

# Grande puissance — Heures Creuses / Heures de Pointe (FCFA/kWh)
# Prime fixe mensuelle (FCFA/kW de puissance souscrite)
SENELEC_GRANDE_PUISSANCE = {
    "DGP": {  # Domestique Grande Puissance
        "hors_pointe": 118.37,
        "de_pointe": 170.53,
        "prime_fixe_kw": 956.13,
    },
    "PGP": {  # Professionnel Grande Puissance
        "hors_pointe": 140.74,
        "de_pointe": 232.23,
        "prime_fixe_kw": 2868.39,
    },
}

# Moyenne tension (FCFA/kWh)
SENELEC_MOYENNE_TENSION = {
    "TCU": {"hors_pointe": 155.50, "de_pointe": 248.28, "prime_fixe_kw": 961.76},
    "TG": {"hors_pointe": 111.91, "de_pointe": 184.65, "prime_fixe_kw": 4093.60},
    "TLU": {"hors_pointe": 91.93, "de_pointe": 151.72, "prime_fixe_kw": 9880.54},
}

# Haute tension (FCFA/kWh)
SENELEC_HAUTE_TENSION = {
    "GENERAL": {"hors_pointe": 71.43, "de_pointe": 108.52, "prime_fixe_kw": 10028.90},
    "SECOURS": {"hors_pointe": 95.12, "de_pointe": 144.49, "prime_fixe_kw": 4458.61},
}

# Proportion typique heures de pointe (19h-23h = 4h/24h ≈ 17%)
# Pour le solaire : production surtout en heures hors pointe → économie sur HP
HP_HOURS_RATIO = 4 / 24  # 16.67%


def compute_bill_tranches(
    monthly_kwh: float,
    tariff_code: str = "DPP",
    use_woyofal: bool = False,
) -> dict:
    """
    Calcule la facture mensuelle Senelec selon les tranches.

    Args:
        monthly_kwh: Consommation mensuelle (kWh)
        tariff_code: DPP, DMP, PPP, PMP
        use_woyofal: Si True, tranche 3 = tarif tranche 2

    Returns:
        dict avec total_xof, breakdown (tranches), tarif_effectif_moyen
    """
    source = SENELEC_WOYOFAL if use_woyofal else SENELEC_TRANCHES
    key = f"{tariff_code}_WOYOFAL" if use_woyofal else tariff_code
    if key not in source:
        key = "DPP" if tariff_code not in SENELEC_TRANCHES else tariff_code
        t1, t2, t3 = SENELEC_TRANCHES.get(key, SENELEC_TRANCHES["DPP"])
    else:
        t1, t2, t3 = source[key]

    kwh_t1 = min(monthly_kwh, TRANCHE_1_MAX)
    kwh_t2 = min(max(0, monthly_kwh - TRANCHE_1_MAX), TRANCHE_2_MAX - TRANCHE_1_MAX)
    kwh_t3 = max(0, monthly_kwh - TRANCHE_2_MAX)

    bill_t1 = kwh_t1 * t1
    bill_t2 = kwh_t2 * t2
    bill_t3 = kwh_t3 * t3
    total = bill_t1 + bill_t2 + bill_t3
    tarif_effectif = total / monthly_kwh if monthly_kwh > 0 else t1

    return {
        "total_xof": round(total, 0),
        "breakdown": {
            "tranche_1_kwh": round(kwh_t1, 1),
            "tranche_2_kwh": round(kwh_t2, 1),
            "tranche_3_kwh": round(kwh_t3, 1),
            "bill_t1_xof": round(bill_t1, 0),
            "bill_t2_xof": round(bill_t2, 0),
            "bill_t3_xof": round(bill_t3, 0),
        },
        "tarif_effectif_moyen_xof_kwh": round(tarif_effectif, 2),
    }


def compute_annual_savings_senelec(
    annual_production_kwh: float,
    annual_consumption_kwh: float,
    tariff_code: str = "DPP",
    use_woyofal: bool = False,
) -> dict:
    """
    Estime les économies annuelles quand la production PV remplace
    l'achat au réseau Senelec.

    Hypothèse simplifiée : la production PV réduit la facture en priorité
    sur les tranches les plus chères (tranche 3 puis 2 puis 1).

    Returns:
        dict avec annual_savings_xof, monthly_before_xof, monthly_after_xof
    """
    monthly_cons = annual_consumption_kwh / 12
    monthly_prod = annual_production_kwh / 12

    bill_before = compute_bill_tranches(monthly_cons, tariff_code, use_woyofal)

    # Consommation nette après PV (on suppose autoconsommation immédiate)
    net_cons = max(0, monthly_cons - monthly_prod)
    bill_after = compute_bill_tranches(net_cons, tariff_code, use_woyofal)

    annual_savings = (bill_before["total_xof"] - bill_after["total_xof"]) * 12

    return {
        "annual_savings_xof": round(annual_savings, 0),
        "monthly_bill_before_xof": bill_before["total_xof"],
        "monthly_bill_after_xof": bill_after["total_xof"],
        "tarif_effectif_xof_kwh": bill_before["tarif_effectif_moyen_xof_kwh"],
    }


def get_tariff_effective_price(
    monthly_consumption_kwh: float,
    tariff_code: str = "DPP",
    use_woyofal: bool = False,
) -> float:
    """
    Retourne le prix effectif moyen (FCFA/kWh) pour une consommation donnée.
    Utile pour la rétrocompatibilité avec le champ electricity_price_kwh.
    """
    r = compute_bill_tranches(monthly_consumption_kwh, tariff_code, use_woyofal)
    return r["tarif_effectif_moyen_xof_kwh"]


# ---------------------------------------------------------------------------
# Codes tarifaires pour l'API
# ---------------------------------------------------------------------------
SENELEC_TARIFF_CODES = [
    "DPP", "DMP", "PPP", "PMP",
    "DPP_WOYOFAL", "DMP_WOYOFAL", "PPP_WOYOFAL", "PMP_WOYOFAL",
]
