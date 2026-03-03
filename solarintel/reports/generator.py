"""
Moteur de génération PDF SolarIntel.

Utilise BaseDocTemplate avec deux PageTemplate :
- cover  : page de garde plein écran
- content : pages avec header/footer persistants
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.platypus.flowables import KeepTogether
from reportlab.graphics.shapes import Drawing, Line

from solarintel.reports.models import SolarReport
from solarintel.reports.theme import ReportTheme
from solarintel.reports.charts import (
    build_monthly_production_chart,
    build_cashflow_chart,
)
from solarintel.config.constants import PVLIB_MODULES, ECONOMIC_DEFAULTS

PAGE_W, PAGE_H = A4
MARGIN = ReportTheme.PAGE_MARGIN


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_number(value: float, decimals: int = 0, suffix: str = "") -> str:
    """Formate un nombre avec séparateur de milliers (espace)."""
    if decimals == 0:
        formatted = f"{value:,.0f}".replace(",", " ")
    else:
        formatted = f"{value:,.{decimals}f}".replace(",", " ")
    return f"{formatted}{suffix}"


def _make_separator() -> Drawing:
    """Trait horizontal fin (séparateur de section)."""
    w = PAGE_W - 2 * MARGIN
    d = Drawing(w, 4)
    d.add(Line(0, 2, w, 2, strokeColor=ReportTheme.BORDER, strokeWidth=0.5))
    return d


def _safe_image(path: str | Path, width: float, height: float) -> RLImage | Spacer:
    """Charge une image si elle existe, sinon retourne un Spacer."""
    if path and os.path.isfile(str(path)):
        return RLImage(str(path), width=width, height=height)
    return Spacer(width, height)


# ---------------------------------------------------------------------------
# Page callbacks
# ---------------------------------------------------------------------------

def _cover_page_callback(canvas, doc):
    """Callback pour la page de garde : fond plein + logo centré."""
    canvas.saveState()
    canvas.setFillColor(ReportTheme.COVER_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()


def _content_header_footer(canvas, doc):
    """Header et footer pour les pages de contenu."""
    canvas.saveState()

    # -- Header --
    top_y = PAGE_H - 12 * mm
    # Logo (petit) à gauche
    logo = getattr(doc, "_logo_path", None)
    if logo and os.path.isfile(logo):
        canvas.drawImage(logo, MARGIN, top_y - 2 * mm, width=10 * mm,
                         height=10 * mm, preserveAspectRatio=True, mask="auto")

    # Company name
    canvas.setFont(ReportTheme.FONT_SANS_BOLD, 9)
    canvas.setFillColor(ReportTheme.PRIMARY_DARK)
    company = getattr(doc, "_company_name", "SolarIntel")
    canvas.drawString(MARGIN + 12 * mm, top_y + 1 * mm, company)

    # Separator line
    canvas.setStrokeColor(ReportTheme.BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, top_y - 4 * mm, PAGE_W - MARGIN, top_y - 4 * mm)

    # -- Footer --
    bottom_y = 10 * mm
    canvas.setFont(ReportTheme.FONT_SANS, 7)
    canvas.setFillColor(ReportTheme.TEXT_LIGHT)

    gen_date = getattr(doc, "_gen_date", date.today().isoformat())
    canvas.drawString(MARGIN, bottom_y, f"Généré le {gen_date}")

    page_num = f"Page {doc.page}"
    canvas.drawRightString(PAGE_W - MARGIN, bottom_y, page_num)

    # Footer separator
    canvas.line(MARGIN, bottom_y + 4 * mm, PAGE_W - MARGIN, bottom_y + 4 * mm)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# ReportGenerator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """Génère un PDF professionnel à partir d'un SolarReport."""

    def __init__(
        self,
        report: SolarReport,
        logo_path: str | Path | None = None,
        company_name: str | None = None,
    ):
        self.report = report
        self.logo_path = str(logo_path) if logo_path else None
        self.company_name = company_name or report.company_name
        self.styles = ReportTheme.get_styles()

    def generate(self, output_path: str = "rapport_solarintel.pdf") -> str:
        """Génère le PDF et retourne le chemin absolu du fichier."""
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN + ReportTheme.HEADER_HEIGHT,
            bottomMargin=MARGIN + ReportTheme.FOOTER_HEIGHT,
        )

        # Pass metadata to callbacks via doc attributes
        doc._logo_path = self.logo_path
        doc._company_name = self.company_name
        doc._gen_date = self.report.generation_date.isoformat()

        # -- Frames --
        cover_frame = Frame(
            0, 0, PAGE_W, PAGE_H,
            leftPadding=MARGIN, rightPadding=MARGIN,
            topPadding=MARGIN, bottomPadding=MARGIN,
            id="cover",
        )
        content_frame = Frame(
            MARGIN,
            MARGIN + ReportTheme.FOOTER_HEIGHT,
            PAGE_W - 2 * MARGIN,
            PAGE_H - 2 * MARGIN - ReportTheme.HEADER_HEIGHT - ReportTheme.FOOTER_HEIGHT,
            id="content",
        )

        doc.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame],
                         onPage=_cover_page_callback),
            PageTemplate(id="content", frames=[content_frame],
                         onPage=_content_header_footer),
        ])

        # Build story
        story = []
        self._add_cover(story)
        self._add_executive_summary(story)
        self._add_system_config(story)
        self._add_simulation(story)
        self._add_economics(story)
        self._add_qa(story)
        self._add_appendix(story)

        doc.build(story)
        return os.path.abspath(output_path)

    # -------------------------------------------------------------------
    # Section 1 : Page de garde
    # -------------------------------------------------------------------
    def _add_cover(self, story: list) -> None:
        s = self.styles

        story.append(Spacer(1, 60 * mm))

        # Logo
        if self.logo_path and os.path.isfile(self.logo_path):
            logo = RLImage(self.logo_path, width=50 * mm, height=50 * mm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 10 * mm))

        story.append(Paragraph(self.report.report_title, s["cover_title"]))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(self.report.system.location_name, s["cover_subtitle"]))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            self.report.generation_date.strftime("%d/%m/%Y"),
            s["cover_subtitle"],
        ))
        story.append(Spacer(1, 15 * mm))
        story.append(Paragraph(self.company_name, s["cover_subtitle"]))

        # Switch to content template for next pages
        story.append(NextPageTemplate("content"))
        story.append(PageBreak())

    # -------------------------------------------------------------------
    # Section 2 : Résumé exécutif
    # -------------------------------------------------------------------
    def _add_executive_summary(self, story: list) -> None:
        s = self.styles
        story.append(Paragraph("1. Résumé exécutif", s["heading1"]))
        story.append(_make_separator())
        story.append(Spacer(1, 3 * mm))

        if self.report.executive_summary:
            story.append(Paragraph(self.report.executive_summary, s["body"]))
        else:
            r = self.report
            summary = (
                f"Ce rapport présente le dimensionnement d'une installation "
                f"photovoltaïque de <b>{_fmt_number(r.system.total_power_kwc, 1)} kWc</b> "
                f"({r.system.panel_count} panneaux {r.system.panel_brand} "
                f"{r.system.panel_power_wc} Wc) "
                f"sur le site de <b>{r.system.location_name}</b>."
                f"<br/><br/>"
                f"La simulation pvlib estime une production annuelle de "
                f"<b>{_fmt_number(r.simulation.annual_production_kwh)} kWh</b> "
                f"avec un ratio de performance de "
                f"<b>{r.simulation.performance_ratio:.1%}</b>. "
                f"L'analyse économique projette un temps de retour sur investissement "
                f"de <b>{r.economics.payback_years:.1f} ans</b> et un LCOE de "
                f"<b>{_fmt_number(r.economics.lcoe_xof_kwh, 1)} {r.economics.currency}/kWh</b>."
            )
            story.append(Paragraph(summary, s["body"]))

        story.append(Spacer(1, 5 * mm))

        # KPI boxes
        kpis = [
            (_fmt_number(self.report.simulation.annual_production_kwh), "kWh/an"),
            (f"{self.report.simulation.performance_ratio:.1%}", "Ratio Perf."),
            (f"{self.report.economics.payback_years:.1f} ans", "Retour Invest."),
            (_fmt_number(self.report.economics.lcoe_xof_kwh, 1), "LCOE (XOF/kWh)"),
        ]
        kpi_data = [
            [Paragraph(v, s["kpi_value"]) for v, _ in kpis],
            [Paragraph(lbl, s["kpi_label"]) for _, lbl in kpis],
        ]
        kpi_table = Table(kpi_data, colWidths=[(PAGE_W - 2 * MARGIN) / 4] * 4)
        kpi_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, ReportTheme.BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, ReportTheme.BORDER),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
            ("BACKGROUND", (0, 0), (-1, -1), ReportTheme.SURFACE),
        ]))
        story.append(kpi_table)

    # -------------------------------------------------------------------
    # Section 3 : Configuration système
    # -------------------------------------------------------------------
    def _add_system_config(self, story: list) -> None:
        s = self.styles
        sys = self.report.system

        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("2. Configuration système", s["heading1"]))
        story.append(_make_separator())

        # Panel specs table
        story.append(Paragraph("2.1 Spécifications panneaux", s["heading2"]))
        panel_data = [
            ["Paramètre", "Valeur"],
            ["Marque / Modèle", f"{sys.panel_brand} {sys.panel_model}"],
            ["Puissance unitaire", f"{sys.panel_power_wc} Wc"],
            ["Efficacité", f"{sys.panel_efficiency:.1%}"],
            ["Nombre de panneaux", str(sys.panel_count)],
            ["Puissance totale", f"{sys.total_power_kwc:.1f} kWc"],
        ]
        story.append(self._build_data_table(panel_data))

        # Location table
        story.append(Paragraph("2.2 Localisation & orientation", s["heading2"]))
        loc_data = [
            ["Paramètre", "Valeur"],
            ["Site", sys.location_name],
            ["Latitude", f"{sys.latitude:.4f}°"],
            ["Longitude", f"{sys.longitude:.4f}°"],
            ["Altitude", f"{sys.altitude:.0f} m"],
            ["Azimut", f"{sys.orientation_azimuth:.0f}° (0°=Nord, 180°=Sud)"],
            ["Inclinaison", f"{sys.tilt:.0f}°"],
        ]
        story.append(self._build_data_table(loc_data))

    # -------------------------------------------------------------------
    # Section 4 : Simulation pvlib
    # -------------------------------------------------------------------
    def _add_simulation(self, story: list) -> None:
        s = self.styles
        sim = self.report.simulation

        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("3. Simulation photovoltaïque", s["heading1"]))
        story.append(_make_separator())

        # KPIs
        story.append(Paragraph("3.1 Indicateurs clés", s["heading2"]))
        sim_data = [
            ["Indicateur", "Valeur"],
            ["Production annuelle", f"{_fmt_number(sim.annual_production_kwh)} kWh"],
            ["Rendement spécifique", f"{_fmt_number(sim.specific_yield_kwh_kwc)} kWh/kWc"],
            ["Performance Ratio", f"{sim.performance_ratio:.1%}"],
        ]
        story.append(self._build_data_table(sim_data))

        # Monthly chart
        story.append(Paragraph("3.2 Production mensuelle", s["heading2"]))
        chart = build_monthly_production_chart(sim.monthly_production_kwh)
        story.append(chart)

        # Losses
        story.append(Paragraph("3.3 Bilan des pertes", s["heading2"]))
        losses_data = [
            ["Source de perte", "Valeur (%)"],
            ["Salissure (soiling)", f"{sim.soiling_loss_pct:.1f}"],
            ["Mismatch", f"{sim.mismatch_loss_pct:.1f}"],
            ["Câblage", f"{sim.wiring_loss_pct:.1f}"],
            ["Disponibilité", f"{sim.availability_loss_pct:.1f}"],
            ["Température", f"{sim.temperature_loss_pct:.1f}"],
            ["Total pertes", f"{sim.total_losses_pct:.1f}"],
        ]
        story.append(self._build_data_table(losses_data))

    # -------------------------------------------------------------------
    # Section 5 : Analyse économique
    # -------------------------------------------------------------------
    def _add_economics(self, story: list) -> None:
        s = self.styles
        eco = self.report.economics

        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("4. Analyse économique", s["heading1"]))
        story.append(_make_separator())

        story.append(Paragraph("4.1 Indicateurs financiers", s["heading2"]))
        eco_data = [
            ["Indicateur", "Valeur"],
            ["Coût total", f"{_fmt_number(eco.total_cost_xof)} {eco.currency}"],
            ["Coût par kWc", f"{_fmt_number(eco.cost_per_kwc_xof)} {eco.currency}/kWc"],
            ["LCOE", f"{_fmt_number(eco.lcoe_xof_kwh, 1)} {eco.currency}/kWh"],
            ["ROI", f"{eco.roi_pct:.1f}%"],
            ["Temps de retour", f"{eco.payback_years:.1f} ans"],
            ["VAN (NPV)", f"{_fmt_number(eco.npv_xof)} {eco.currency}"],
            ["Économie annuelle", f"{_fmt_number(eco.annual_savings_xof)} {eco.currency}/an"],
        ]
        story.append(self._build_data_table(eco_data))

        # Cashflow chart
        if any(v != 0 for v in eco.cashflow_cumulative):
            story.append(Paragraph("4.2 Flux de trésorerie cumulé (25 ans)", s["heading2"]))
            chart = build_cashflow_chart(eco.cashflow_cumulative)
            story.append(chart)

    # -------------------------------------------------------------------
    # Section 6 : Rapport QA
    # -------------------------------------------------------------------
    def _add_qa(self, story: list) -> None:
        s = self.styles
        qa = self.report.qa

        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("5. Rapport Qualité & Validation", s["heading1"]))
        story.append(_make_separator())

        if qa.validations:
            story.append(Paragraph("5.1 Matrice de validation", s["heading2"]))
            val_data = [["Code", "Critère", "Statut", "Détail"]]
            for v in qa.validations:
                val_data.append([v.code, v.label, v.status, v.detail])
            story.append(self._build_qa_table(val_data))

        if qa.edge_cases:
            story.append(Paragraph("5.2 Cas limites (edge cases)", s["heading2"]))
            ec_data = [["Code", "Critère", "Statut", "Détail"]]
            for ec in qa.edge_cases:
                ec_data.append([ec.code, ec.label, ec.status, ec.detail])
            story.append(self._build_qa_table(ec_data))

        # Verdict
        story.append(Spacer(1, 3 * mm))
        verdict_color = ReportTheme.SUCCESS if qa.verdict == "PASS" else ReportTheme.ERROR
        verdict_style = self.styles["kpi_value"].clone(
            "verdict", textColor=verdict_color, fontSize=18,
        )
        story.append(Paragraph(f"Verdict : {qa.verdict}", verdict_style))

        if qa.notes:
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(qa.notes, s["body_small"]))

    # -------------------------------------------------------------------
    # Section 7 : Annexes
    # -------------------------------------------------------------------
    def _add_appendix(self, story: list) -> None:
        s = self.styles

        story.append(PageBreak())
        story.append(Paragraph("6. Annexes", s["heading1"]))
        story.append(_make_separator())

        # pvlib modules
        story.append(Paragraph("6.1 Modules pvlib utilisés", s["heading2"]))
        for mod in PVLIB_MODULES:
            story.append(Paragraph(f"• <font face='Courier' size='8'>{mod}</font>", s["body_small"]))

        # Economic constants
        story.append(Paragraph("6.2 Constantes économiques", s["heading2"]))
        for k, v in ECONOMIC_DEFAULTS.items():
            story.append(Paragraph(
                f"• <b>{k}</b> : {v}",
                s["body_small"],
            ))

        # Methodology
        story.append(Paragraph("6.3 Méthodologie", s["heading2"]))
        methodology = (
            "La simulation utilise la chaîne pvlib : récupération des données TMY "
            "(Typical Meteorological Year) via PVGIS, modélisation du système PV "
            "avec ModelChain, calcul des pertes (salissure, mismatch, câblage, "
            "température, disponibilité). L'analyse économique se base sur le tarif "
            "SENELEC, une dégradation annuelle de 0.5%, et une durée de vie de 25 ans."
        )
        story.append(Paragraph(methodology, s["body"]))

        # Formulas
        story.append(Paragraph("6.4 Formules clés", s["heading2"]))
        formulas = [
            ("LCOE", "Coût total / (Σ Production année_i × (1 - dégradation)^i)"),
            ("ROI", "(Économie totale - Coût) / Coût × 100"),
            ("Payback", "Année où cashflow cumulé ≥ 0"),
            ("PR", "Production réelle / Production théorique (STC)"),
        ]
        for name, formula in formulas:
            story.append(Paragraph(
                f"• <b>{name}</b> = <font face='Courier' size='8'>{formula}</font>",
                s["body_small"],
            ))

        # Raw crew output (if available)
        if self.report.raw_crew_output:
            story.append(PageBreak())
            story.append(Paragraph("6.5 Sortie brute CrewAI", s["heading2"]))
            # Truncate if very long
            raw = self.report.raw_crew_output
            if len(raw) > 5000:
                raw = raw[:5000] + "\n\n[... tronqué ...]"
            for line in raw.split("\n"):
                # Escape XML entities for ReportLab
                line = (line.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))
                story.append(Paragraph(line or "&nbsp;", s["mono"]))

    # -------------------------------------------------------------------
    # Table helpers
    # -------------------------------------------------------------------
    def _build_data_table(self, data: list[list[str]]) -> Table:
        """Construit un tableau 2 colonnes (paramètre / valeur)."""
        col_w = (PAGE_W - 2 * MARGIN) / 2
        table = Table(data, colWidths=[col_w, col_w])

        style_cmds = [
            ("FONTNAME", (0, 0), (-1, 0), ReportTheme.FONT_SANS_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), ReportTheme.TABLE_HEADER_TEXT),
            ("BACKGROUND", (0, 0), (-1, 0), ReportTheme.TABLE_HEADER_BG),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, ReportTheme.BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        # Alternate row colors
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(
                    ("BACKGROUND", (0, i), (-1, i), ReportTheme.TABLE_ROW_ALT)
                )

        table.setStyle(TableStyle(style_cmds))
        return table

    def _build_qa_table(self, data: list[list[str]]) -> Table:
        """Construit un tableau QA avec coloration PASS/FAIL."""
        col_widths = [18 * mm, 60 * mm, 20 * mm, None]
        # Calculate last column
        remaining = PAGE_W - 2 * MARGIN - sum(w for w in col_widths if w)
        col_widths[-1] = remaining

        table = Table(data, colWidths=col_widths)

        style_cmds = [
            ("FONTNAME", (0, 0), (-1, 0), ReportTheme.FONT_SANS_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 0), (-1, 0), ReportTheme.TABLE_HEADER_TEXT),
            ("BACKGROUND", (0, 0), (-1, 0), ReportTheme.TABLE_HEADER_BG),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, ReportTheme.BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        # Color-code status cells
        for i in range(1, len(data)):
            status = data[i][2] if len(data[i]) > 2 else ""
            if status == "PASS":
                style_cmds.append(
                    ("TEXTCOLOR", (2, i), (2, i), ReportTheme.SUCCESS)
                )
            elif status == "FAIL":
                style_cmds.append(
                    ("TEXTCOLOR", (2, i), (2, i), ReportTheme.ERROR)
                )
            elif status == "WARNING":
                style_cmds.append(
                    ("TEXTCOLOR", (2, i), (2, i), ReportTheme.WARNING)
                )
            if i % 2 == 0:
                style_cmds.append(
                    ("BACKGROUND", (0, i), (-1, i), ReportTheme.TABLE_ROW_ALT)
                )

        table.setStyle(TableStyle(style_cmds))
        return table
