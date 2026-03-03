"""
Graphiques vectoriels ReportLab pour les rapports SolarIntel.
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

from solarintel.reports.theme import ReportTheme

MONTHS_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc",
]


def build_monthly_production_chart(
    monthly_kwh: list[float],
    width: float = 170 * mm,
    height: float = 100 * mm,
) -> Drawing:
    """Graphique à barres de la production mensuelle (12 barres)."""
    d = Drawing(width, height)

    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 35
    chart.width = width - 70
    chart.height = height - 60

    chart.data = [monthly_kwh]
    chart.categoryAxis.categoryNames = MONTHS_FR
    chart.categoryAxis.labels.fontName = ReportTheme.FONT_SANS
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.angle = 0

    chart.valueAxis.valueMin = 0
    max_val = max(monthly_kwh) if monthly_kwh and max(monthly_kwh) > 0 else 100
    chart.valueAxis.valueMax = max_val * 1.15
    chart.valueAxis.valueStep = round(max_val / 5, -1) or 10
    chart.valueAxis.labels.fontName = ReportTheme.FONT_SANS
    chart.valueAxis.labels.fontSize = 8

    chart.bars[0].fillColor = ReportTheme.PRIMARY
    chart.bars[0].strokeColor = ReportTheme.PRIMARY_DARK
    chart.bars[0].strokeWidth = 0.5
    chart.barWidth = 8

    d.add(chart)

    # Y-axis label
    d.add(String(10, height / 2, "kWh", fontName=ReportTheme.FONT_SANS,
                 fontSize=9, fillColor=ReportTheme.TEXT_SECONDARY))

    return d


def build_cashflow_chart(
    cashflow_cumulative: list[float],
    width: float = 170 * mm,
    height: float = 100 * mm,
) -> Drawing:
    """Graphique linéaire du flux de trésorerie cumulé sur 25 ans."""
    n_years = len(cashflow_cumulative)
    d = Drawing(width, height)

    chart = HorizontalLineChart()
    chart.x = 50
    chart.y = 35
    chart.width = width - 80
    chart.height = height - 60

    chart.data = [cashflow_cumulative]

    chart.categoryAxis.categoryNames = [str(i) for i in range(n_years)]
    chart.categoryAxis.labels.fontName = ReportTheme.FONT_SANS
    chart.categoryAxis.labels.fontSize = 7
    # Show every 5 years to avoid crowding
    for i in range(n_years):
        if i % 5 != 0:
            chart.categoryAxis.labels[i].visible = 0

    min_val = min(cashflow_cumulative) if cashflow_cumulative else -1_000_000
    max_val = max(cashflow_cumulative) if cashflow_cumulative else 1_000_000
    chart.valueAxis.valueMin = min_val * 1.1 if min_val < 0 else 0
    chart.valueAxis.valueMax = max_val * 1.15 if max_val > 0 else 100
    chart.valueAxis.labels.fontName = ReportTheme.FONT_SANS
    chart.valueAxis.labels.fontSize = 7

    chart.lines[0].strokeColor = ReportTheme.ACCENT
    chart.lines[0].strokeWidth = 2

    d.add(chart)

    # Axis labels
    d.add(String(5, height / 2, "XOF", fontName=ReportTheme.FONT_SANS,
                 fontSize=9, fillColor=ReportTheme.TEXT_SECONDARY))
    d.add(String(width / 2, 5, "Année", fontName=ReportTheme.FONT_SANS,
                 fontSize=9, fillColor=ReportTheme.TEXT_SECONDARY))

    return d
