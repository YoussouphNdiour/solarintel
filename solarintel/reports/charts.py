"""
Graphiques vectoriels ReportLab pour les rapports SolarIntel.
Tous les graphiques sont rendus via VerticalBarChart / HorizontalLineChart
(pas de dépendance matplotlib).
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, String, Rect, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

MONTHS_FR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
             "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

C_PURPLE = HexColor("#A78BFA")
C_ORANGE = HexColor("#F97316")

C_PRIMARY      = HexColor("#0EA5E9")
C_PRIMARY_DARK = HexColor("#0369A1")
C_AMBER        = HexColor("#F59E0B")
C_GREEN        = HexColor("#22C55E")
C_TEXT         = HexColor("#0F172A")
C_TEXT_SEC     = HexColor("#475569")
C_BORDER       = HexColor("#CBD5E1")
C_BG           = HexColor("#F8FAFC")
C_RED          = HexColor("#EF4444")


def _safe_step(max_val: float, divisions: int = 4) -> float:
    """Calcule un valueStep non nul et lisible."""
    if max_val <= 0:
        return 10
    raw = max_val / divisions
    # Arrondir à la puissance de 10 supérieure
    import math
    magnitude = 10 ** math.floor(math.log10(raw))
    step = max(magnitude, round(raw / magnitude) * magnitude)
    return max(step, 1)


def build_monthly_production_chart(
    monthly_kwh: list[float],
    width: float = 160 * mm,
    height: float = 90 * mm,
) -> Drawing:
    """Graphique barres de production mensuelle — 12 mois avec fond stylisé."""
    d = Drawing(width, height)

    # Fond avec bordure
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.8))

    # Bande titre
    d.add(Rect(0, height - 14, width, 14, fillColor=C_PRIMARY_DARK, strokeColor=None, strokeWidth=0))

    values = [float(v) for v in monthly_kwh] if monthly_kwh else []

    if not values or max(values) <= 0:
        d.add(String(
            width / 2, height / 2,
            "Données de production non disponibles",
            fontName="Helvetica", fontSize=9,
            fillColor=C_TEXT_SEC, textAnchor="middle",
        ))
        return d

    # Titre dans la bande bleue
    d.add(String(
        width / 2, height - 10,
        "Production mensuelle estimée (kWh)",
        fontName="Helvetica-Bold", fontSize=8.5,
        fillColor=HexColor("#FFFFFF"), textAnchor="middle",
    ))

    chart = VerticalBarChart()
    chart.x = 48
    chart.y = 32
    chart.width  = width  - 64
    chart.height = height - 58

    chart.data = [values]

    chart.categoryAxis.categoryNames = MONTHS_FR
    chart.categoryAxis.labels.fontName  = "Helvetica"
    chart.categoryAxis.labels.fontSize  = 7
    chart.categoryAxis.labels.angle     = 0
    chart.categoryAxis.tickUp           = 0
    chart.categoryAxis.tickDown         = 2
    chart.categoryAxis.strokeColor      = C_BORDER
    chart.categoryAxis.strokeWidth      = 0.5

    max_val = max(values)
    chart.valueAxis.valueMin    = 0
    chart.valueAxis.valueMax    = max_val * 1.25
    chart.valueAxis.valueStep   = _safe_step(max_val * 1.25, 4)
    chart.valueAxis.labels.fontName  = "Helvetica"
    chart.valueAxis.labels.fontSize  = 6.5
    chart.valueAxis.strokeColor      = C_BORDER
    chart.valueAxis.strokeWidth      = 0.5
    chart.valueAxis.gridStrokeColor  = HexColor("#E2E8F0")
    chart.valueAxis.gridStrokeWidth  = 0.3

    # Colorer les barres par intensité (amber = max, bleu clair = min)
    chart.bars[0].fillColor   = C_PRIMARY
    chart.bars[0].strokeColor = C_PRIMARY_DARK
    chart.bars[0].strokeWidth = 0.3
    chart.groupSpacing        = 4

    d.add(chart)

    # Étiquette axe Y
    d.add(String(
        8, height / 2,
        "kWh", fontName="Helvetica", fontSize=7.5,
        fillColor=C_TEXT_SEC, textAnchor="middle",
    ))

    # Valeur max annotée en amber
    max_idx = values.index(max_val)
    bar_w = chart.width / 12
    d.add(Rect(
        chart.x + max_idx * bar_w, chart.y + chart.height + 2,
        bar_w, 8,
        fillColor=C_AMBER, strokeColor=None, strokeWidth=0,
    ))
    d.add(String(
        chart.x + (max_idx + 0.5) * bar_w,
        chart.y + chart.height + 3.5,
        f"{max_val:,.0f}",
        fontName="Helvetica-Bold", fontSize=6,
        fillColor=HexColor("#1E293B"), textAnchor="middle",
    ))

    # Étiquette axe X
    d.add(String(
        chart.x + chart.width / 2, 12,
        "Mois", fontName="Helvetica", fontSize=7.5,
        fillColor=C_TEXT_SEC, textAnchor="middle",
    ))

    # Total annuel
    total = sum(values)
    d.add(String(
        width - 6, 12,
        f"Total : {total:,.0f} kWh/an",
        fontName="Helvetica-Bold", fontSize=7,
        fillColor=C_PRIMARY_DARK, textAnchor="end",
    ))

    return d


def build_cashflow_chart(
    cashflow_cumulative: list[float],
    width: float = 160 * mm,
    height: float = 80 * mm,
) -> Drawing:
    """Graphique linéaire du flux de trésorerie cumulé sur 25 ans."""
    d = Drawing(width, height)

    # Fond
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.5))

    values = [float(v) for v in cashflow_cumulative] if cashflow_cumulative else []
    n = len(values)

    if n < 2 or all(v == 0 for v in values):
        d.add(String(
            width / 2, height / 2,
            "Données de trésorerie non disponibles",
            fontName="Helvetica", fontSize=9,
            fillColor=C_TEXT_SEC, textAnchor="middle",
        ))
        return d

    # Titre
    d.add(String(
        width / 2, height - 10,
        "Flux de trésorerie cumulé sur 25 ans",
        fontName="Helvetica-Bold", fontSize=9,
        fillColor=C_TEXT, textAnchor="middle",
    ))

    chart = HorizontalLineChart()
    chart.x      = 52
    chart.y      = 28
    chart.width  = width  - 68
    chart.height = height - 50

    chart.data = [values]
    chart.categoryAxis.categoryNames = [str(i) for i in range(n)]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 6
    chart.categoryAxis.strokeColor     = C_BORDER
    chart.categoryAxis.strokeWidth     = 0.5

    # Afficher seulement tous les 5 ans
    for i in range(n):
        if i % 5 != 0:
            chart.categoryAxis.labels[i].visible = 0

    min_val = min(values)
    max_val = max(values)
    v_min = min_val * 1.15 if min_val < 0 else -(max_val * 0.05)
    v_max = max_val * 1.15 if max_val > 0 else 100

    chart.valueAxis.valueMin   = v_min
    chart.valueAxis.valueMax   = v_max
    chart.valueAxis.valueStep  = _safe_step(abs(v_max - v_min), 4)
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6
    chart.valueAxis.strokeColor     = C_BORDER
    chart.valueAxis.strokeWidth     = 0.5

    chart.lines[0].strokeColor = C_GREEN
    chart.lines[0].strokeWidth = 2

    d.add(chart)

    # Ligne zéro (axe de rentabilité)
    if v_min < 0 < v_max:
        zero_ratio = abs(v_min) / (abs(v_min) + v_max)
        zero_y = chart.y + zero_ratio * chart.height
        d.add(Line(
            chart.x, zero_y, chart.x + chart.width, zero_y,
            strokeColor=C_AMBER, strokeWidth=1, strokeDashArray=[3, 2],
        ))
        d.add(String(
            chart.x - 2, zero_y + 2,
            "0", fontName="Helvetica", fontSize=6,
            fillColor=C_AMBER, textAnchor="end",
        ))

    # Labels axes
    d.add(String(
        10, height / 2,
        "XOF", fontName="Helvetica", fontSize=8,
        fillColor=C_TEXT_SEC, textAnchor="middle",
    ))
    d.add(String(
        width / 2, 8,
        "Année", fontName="Helvetica", fontSize=8,
        fillColor=C_TEXT_SEC, textAnchor="middle",
    ))

    return d


# ── Nouveaux graphiques ────────────────────────────────────────────────────────

def build_load_profile_chart(
    appliances: list,
    width: float = 160 * mm,
    height: float = 80 * mm,
) -> Drawing:
    """Courbe de charge journalière 0h-23h issue du bilan énergétique."""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.8))
    d.add(Rect(0, height - 14, width, 14, fillColor=C_PRIMARY_DARK, strokeColor=None, strokeWidth=0))
    d.add(String(width / 2, height - 10,
                 "Profil de charge journalier (kW)",
                 fontName="Helvetica-Bold", fontSize=8.5,
                 fillColor=HexColor("#FFFFFF"), textAnchor="middle"))

    DAY_SLOTS   = list(range(6, 18))
    NIGHT_SLOTS = list(range(18, 24)) + list(range(0, 6))
    hourly = [0.0] * 24
    for a in appliances:
        qty = a.get("qty", 1) or 1
        pw  = a.get("power", 0) or 0
        hd  = min(float(a.get("hoursDay",   0) or 0), 12)
        hn  = min(float(a.get("hoursNight", 0) or 0), 12)
        kw  = qty * pw / 1000
        for h in DAY_SLOTS:
            hourly[h] += kw * (hd / 12)
        for h in NIGHT_SLOTS:
            hourly[h] += kw * (hn / 12)

    max_val = max(hourly) if any(v > 0 for v in hourly) else 1.0
    chart = VerticalBarChart()
    chart.x      = 46
    chart.y      = 28
    chart.width  = width  - 58
    chart.height = height - 52
    chart.data   = [hourly]
    chart.categoryAxis.categoryNames    = [str(h) if h % 6 == 0 else "" for h in range(24)]
    chart.categoryAxis.labels.fontName  = "Helvetica"
    chart.categoryAxis.labels.fontSize  = 6.5
    chart.categoryAxis.tickUp           = 0
    chart.categoryAxis.tickDown         = 2
    chart.categoryAxis.strokeColor      = C_BORDER
    chart.categoryAxis.strokeWidth      = 0.5
    chart.valueAxis.valueMin    = 0
    chart.valueAxis.valueMax    = max_val * 1.3
    chart.valueAxis.valueStep   = _safe_step(max_val * 1.3, 4)
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6
    chart.valueAxis.strokeColor     = C_BORDER
    chart.valueAxis.strokeWidth     = 0.5
    chart.valueAxis.gridStrokeColor = HexColor("#E2E8F0")
    chart.valueAxis.gridStrokeWidth = 0.3
    chart.bars[0].fillColor   = C_PRIMARY
    chart.bars[0].strokeColor = C_PRIMARY_DARK
    chart.bars[0].strokeWidth = 0.2
    chart.groupSpacing        = 1
    d.add(chart)

    sol_x1 = chart.x + 6  * (chart.width / 24)
    sol_x2 = chart.x + 18 * (chart.width / 24)
    sol_y  = chart.y - 8
    d.add(Line(sol_x1, sol_y, sol_x2, sol_y, strokeColor=C_AMBER, strokeWidth=1.5))
    d.add(String((sol_x1 + sol_x2) / 2, sol_y - 7,
                 "Production solaire disponible (06h-18h)",
                 fontName="Helvetica", fontSize=5.5, fillColor=C_AMBER, textAnchor="middle"))
    d.add(String(width - 4, 10, f"Pic : {max_val:.2f} kW",
                 fontName="Helvetica-Bold", fontSize=7, fillColor=C_RED, textAnchor="end"))
    d.add(String(8, height / 2, "kW",
                 fontName="Helvetica", fontSize=7, fillColor=C_TEXT_SEC, textAnchor="middle"))
    d.add(String(chart.x + chart.width / 2, 8, "Heure",
                 fontName="Helvetica", fontSize=7, fillColor=C_TEXT_SEC, textAnchor="middle"))
    return d


def build_monthly_comparison_chart(
    monthly_prod: list[float],
    monthly_cons: list[float],
    width: float = 160 * mm,
    height: float = 85 * mm,
) -> Drawing:
    """Barres groupées Production vs Consommation mensuelle (kWh) sur 12 mois."""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.8))
    d.add(Rect(0, height - 14, width, 14, fillColor=C_PRIMARY_DARK, strokeColor=None, strokeWidth=0))
    d.add(String(width / 2, height - 10,
                 "Production vs Consommation mensuelle (kWh)",
                 fontName="Helvetica-Bold", fontSize=8.5,
                 fillColor=HexColor("#FFFFFF"), textAnchor="middle"))

    prod = [float(v) for v in (monthly_prod or [])] or [0.0] * 12
    cons = [float(v) for v in (monthly_cons or [])] or [0.0] * 12
    max_val = max(max(prod, default=0), max(cons, default=0)) or 100

    chart = VerticalBarChart()
    chart.x      = 48
    chart.y      = 28
    chart.width  = width  - 64
    chart.height = height - 54
    chart.data   = [prod, cons]
    chart.categoryAxis.categoryNames    = MONTHS_FR
    chart.categoryAxis.labels.fontName  = "Helvetica"
    chart.categoryAxis.labels.fontSize  = 7
    chart.categoryAxis.tickUp           = 0
    chart.categoryAxis.tickDown         = 2
    chart.categoryAxis.strokeColor      = C_BORDER
    chart.categoryAxis.strokeWidth      = 0.5
    chart.valueAxis.valueMin    = 0
    chart.valueAxis.valueMax    = max_val * 1.25
    chart.valueAxis.valueStep   = _safe_step(max_val * 1.25, 4)
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6
    chart.valueAxis.strokeColor     = C_BORDER
    chart.valueAxis.strokeWidth     = 0.5
    chart.valueAxis.gridStrokeColor = HexColor("#E2E8F0")
    chart.valueAxis.gridStrokeWidth = 0.3
    chart.bars[0].fillColor   = C_PRIMARY
    chart.bars[0].strokeColor = C_PRIMARY_DARK
    chart.bars[0].strokeWidth = 0.3
    chart.bars[1].fillColor   = C_AMBER
    chart.bars[1].strokeColor = HexColor("#B45309")
    chart.bars[1].strokeWidth = 0.3
    chart.groupSpacing = 4
    d.add(chart)

    lx = chart.x
    d.add(Rect(lx,      10, 8, 5, fillColor=C_PRIMARY, strokeColor=None, strokeWidth=0))
    d.add(String(lx + 10, 12, "Production",
                 fontName="Helvetica", fontSize=6, fillColor=C_TEXT, textAnchor="start"))
    d.add(Rect(lx + 62, 10, 8, 5, fillColor=C_AMBER, strokeColor=None, strokeWidth=0))
    d.add(String(lx + 74, 12, "Consommation",
                 fontName="Helvetica", fontSize=6, fillColor=C_TEXT, textAnchor="start"))
    d.add(String(8, height / 2, "kWh",
                 fontName="Helvetica", fontSize=7, fillColor=C_TEXT_SEC, textAnchor="middle"))
    return d


def build_senelec_billing_chart(
    monthly_before: list[float],
    monthly_after: list[float],
    width: float = 160 * mm,
    height: float = 85 * mm,
) -> Drawing:
    """Barres groupées : Facture avant / après / économie SENELEC — 12 mois (FCFA)."""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.8))
    d.add(Rect(0, height - 14, width, 14, fillColor=C_PRIMARY_DARK, strokeColor=None, strokeWidth=0))
    d.add(String(width / 2, height - 10,
                 "Facture SENELEC : Avant / Après solaire (FCFA)",
                 fontName="Helvetica-Bold", fontSize=8.5,
                 fillColor=HexColor("#FFFFFF"), textAnchor="middle"))

    before  = [float(v) for v in (monthly_before or [])] or [0.0] * 12
    after   = [float(v) for v in (monthly_after  or [])] or [0.0] * 12
    savings = [max(0.0, b - a) for b, a in zip(before, after)]
    max_val = max(max(before, default=0), 1)

    chart = VerticalBarChart()
    chart.x      = 52
    chart.y      = 28
    chart.width  = width  - 68
    chart.height = height - 54
    chart.data   = [before, after, savings]
    chart.categoryAxis.categoryNames    = MONTHS_FR
    chart.categoryAxis.labels.fontName  = "Helvetica"
    chart.categoryAxis.labels.fontSize  = 7
    chart.categoryAxis.tickUp           = 0
    chart.categoryAxis.tickDown         = 2
    chart.categoryAxis.strokeColor      = C_BORDER
    chart.categoryAxis.strokeWidth      = 0.5
    chart.valueAxis.valueMin    = 0
    chart.valueAxis.valueMax    = max_val * 1.25
    chart.valueAxis.valueStep   = _safe_step(max_val * 1.25, 4)
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 5.5
    chart.valueAxis.strokeColor     = C_BORDER
    chart.valueAxis.strokeWidth     = 0.5
    chart.valueAxis.gridStrokeColor = HexColor("#E2E8F0")
    chart.valueAxis.gridStrokeWidth = 0.3
    chart.bars[0].fillColor   = C_RED
    chart.bars[0].strokeColor = HexColor("#B91C1C")
    chart.bars[0].strokeWidth = 0.3
    chart.bars[1].fillColor   = C_PRIMARY
    chart.bars[1].strokeColor = C_PRIMARY_DARK
    chart.bars[1].strokeWidth = 0.3
    chart.bars[2].fillColor   = C_GREEN
    chart.bars[2].strokeColor = HexColor("#15803D")
    chart.bars[2].strokeWidth = 0.3
    chart.groupSpacing = 4
    d.add(chart)

    lx = chart.x
    for i, (color, label) in enumerate([
        (C_RED,     "Avant solaire"),
        (C_PRIMARY, "Après solaire"),
        (C_GREEN,   "Économie"),
    ]):
        ox = lx + i * 52
        d.add(Rect(ox, 10, 8, 5, fillColor=color, strokeColor=None, strokeWidth=0))
        d.add(String(ox + 10, 12, label,
                     fontName="Helvetica", fontSize=6,
                     fillColor=C_TEXT, textAnchor="start"))
    d.add(String(10, height / 2, "FCFA",
                 fontName="Helvetica", fontSize=7,
                 fillColor=C_TEXT_SEC, textAnchor="middle"))
    total_savings = sum(savings)
    d.add(String(width - 4, 12,
                 f"Economie annuelle : {total_savings:,.0f} FCFA",
                 fontName="Helvetica-Bold", fontSize=7,
                 fillColor=C_GREEN, textAnchor="end"))
    return d


def build_usage_category_chart(
    appliances: list,
    width: float = 160 * mm,
    height: float = 75 * mm,
) -> Drawing:
    """Barres horizontales de repartition par usage (kWh/jour)."""
    CATEGORIES = [
        ("Climatisation", ["clim", "pompe", "moteur", "ventil"], C_ORANGE),
        ("Refrigeration",  ["frigo", "refrig", "congel"],          HexColor("#38BDF8")),
        ("Eclairage",      ["eclairage", "led", "lampe", "lumiere"], C_AMBER),
        ("Audiovisuel",    ["tv", "television", "ecran", "video"],  C_PURPLE),
        ("Informatique",   ["ordinateur", "pc", "laptop", "chargeur", "info"], C_GREEN),
        ("Autres",         [], C_TEXT_SEC),
    ]

    totals: dict[str, float] = {name: 0.0 for name, _, _ in CATEGORIES}
    for a in appliances:
        raw  = (a.get("name", "") or "").lower()
        # normalize accents for matching
        name = (raw.replace("\xe9", "e").replace("\xe8", "e").replace("\xea", "e")
                    .replace("\xe0", "a").replace("\xf4", "o").replace("\xf9", "u"))
        kwh  = (a.get("qty", 1) or 1) * (a.get("power", 0) or 0) * (
            (a.get("hoursDay", 0) or 0) + (a.get("hoursNight", 0) or 0)
        ) / 1000
        matched = False
        for cat, keywords, _ in CATEGORIES[:-1]:
            if any(kw in name for kw in keywords):
                totals[cat] += kwh
                matched = True
                break
        if not matched:
            totals["Autres"] += kwh

    data = [(cat, totals[cat], color)
            for cat, _, color in CATEGORIES if totals.get(cat, 0) > 0]
    data.sort(key=lambda x: x[1], reverse=True)

    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.8))
    d.add(Rect(0, height - 14, width, 14, fillColor=C_PRIMARY_DARK, strokeColor=None, strokeWidth=0))
    d.add(String(width / 2, height - 10,
                 "Repartition de la consommation par usage (kWh/jour)",
                 fontName="Helvetica-Bold", fontSize=8.5,
                 fillColor=HexColor("#FFFFFF"), textAnchor="middle"))

    if not data:
        d.add(String(width / 2, height / 2, "Aucune donnee",
                     fontName="Helvetica", fontSize=9,
                     fillColor=C_TEXT_SEC, textAnchor="middle"))
        return d

    total  = sum(v for _, v, _ in data) or 1.0
    max_v  = data[0][1] if data else 1.0
    bar_area_w = width - 110
    bar_h  = 9
    gap    = 5
    start_y = height - 26

    for i, (cat, val, color) in enumerate(data):
        y     = start_y - i * (bar_h + gap)
        bar_w = (val / max_v) * bar_area_w if max_v > 0 else 0
        d.add(Rect(88, y, bar_w, bar_h, fillColor=color, strokeColor=None, strokeWidth=0))
        d.add(String(86, y + 1.5, cat,
                     fontName="Helvetica", fontSize=7,
                     fillColor=C_TEXT, textAnchor="end"))
        pct = val / total * 100
        d.add(String(92 + bar_w, y + 1.5,
                     f"{val:.2f} kWh  {pct:.0f}%",
                     fontName="Helvetica-Bold", fontSize=6,
                     fillColor=C_TEXT, textAnchor="start"))
    return d
