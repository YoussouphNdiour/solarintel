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
    height: float = 80 * mm,
) -> Drawing:
    """Graphique barres de production mensuelle — 12 mois."""
    d = Drawing(width, height)

    # Fond
    d.add(Rect(0, 0, width, height, fillColor=C_BG, strokeColor=C_BORDER, strokeWidth=0.5))

    values = [float(v) for v in monthly_kwh] if monthly_kwh else []

    if not values or max(values) <= 0:
        d.add(String(
            width / 2, height / 2,
            "Données de production non disponibles",
            fontName="Helvetica", fontSize=9,
            fillColor=C_TEXT_SEC, textAnchor="middle",
        ))
        return d

    # Titre
    d.add(String(
        width / 2, height - 10,
        "Production mensuelle (kWh)",
        fontName="Helvetica-Bold", fontSize=9,
        fillColor=C_TEXT, textAnchor="middle",
    ))

    chart = VerticalBarChart()
    chart.x = 44
    chart.y = 28
    chart.width  = width  - 60
    chart.height = height - 50

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
    chart.valueAxis.valueMax    = max_val * 1.2
    chart.valueAxis.valueStep   = _safe_step(max_val * 1.2, 4)
    chart.valueAxis.labels.fontName  = "Helvetica"
    chart.valueAxis.labels.fontSize  = 7
    chart.valueAxis.strokeColor      = C_BORDER
    chart.valueAxis.strokeWidth      = 0.5

    chart.bars[0].fillColor   = C_PRIMARY
    chart.bars[0].strokeColor = C_PRIMARY_DARK
    chart.bars[0].strokeWidth = 0.3
    chart.groupSpacing        = 3

    d.add(chart)

    # Étiquette axe Y
    d.add(String(
        10, height / 2,
        "kWh", fontName="Helvetica", fontSize=8,
        fillColor=C_TEXT_SEC, textAnchor="middle",
    ))

    # Valeur max annotée
    max_idx = values.index(max_val)
    d.add(String(
        chart.x + (max_idx + 0.5) * (chart.width / 12),
        chart.y + chart.height + 4,
        f"{max_val:,.0f}",
        fontName="Helvetica-Bold", fontSize=6,
        fillColor=C_AMBER, textAnchor="middle",
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
