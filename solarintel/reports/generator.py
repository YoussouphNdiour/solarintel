"""
Moteur de génération PDF SolarIntel — Design professionnel v2.
Cover page dessinée sur canvas. Pages contenu avec header/footer.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

from solarintel.reports.models import SolarReport
from solarintel.reports.theme import ReportTheme
from solarintel.reports.charts import build_monthly_production_chart, build_cashflow_chart
from solarintel.config.constants import PVLIB_MODULES, ECONOMIC_DEFAULTS

PAGE_W, PAGE_H = A4
MARGIN = ReportTheme.PAGE_MARGIN
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Palette ──────────────────────────────────────────────────────────────────
C_PRIMARY      = HexColor("#0EA5E9")
C_PRIMARY_DARK = HexColor("#0369A1")
C_NAVY         = HexColor("#0F172A")
C_AMBER        = HexColor("#F59E0B")
C_GREEN        = HexColor("#22C55E")
C_RED          = HexColor("#EF4444")
C_WHITE        = HexColor("#FFFFFF")
C_SURFACE      = HexColor("#F8FAFC")
C_BORDER       = HexColor("#E2E8F0")
C_TEXT         = HexColor("#0F172A")
C_TEXT_SEC     = HexColor("#475569")
C_TEXT_LIGHT   = HexColor("#94A3B8")
C_ROW_ALT      = HexColor("#F1F5F9")

# ── Active theme (overridden per-report, safe for synchronous generation) ─────
_THEME: dict = {"primary": C_PRIMARY, "secondary": C_PRIMARY_DARK}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(value: float, decimals: int = 0, suffix: str = "") -> str:
    if decimals == 0:
        s = f"{value:,.0f}".replace(",", "\u202f")
    else:
        s = f"{value:,.{decimals}f}".replace(",", "\u202f")
    return f"{s}{suffix}"


def _section_header(text: str, color=None) -> Table:
    """Bande colorée pleine largeur pour les titres de section."""
    bg = color or _THEME["secondary"]
    para = Paragraph(
        text,
        ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=11,
                       textColor=C_WHITE, leading=15),
    )
    t = Table([[para]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    t.spaceBefore = 8 * mm
    t.spaceAfter  = 4 * mm
    return t


def _subsection_header(text: str) -> Table:
    """Sous-titre avec barre gauche colorée."""
    para = Paragraph(
        text,
        ParagraphStyle("ssh", fontName="Helvetica-Bold", fontSize=10,
                       textColor=_THEME["secondary"], leading=13),
    )
    t = Table([[para]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), HexColor("#EFF6FF")),
        ("LINEAFTER",     (0, 0), (-1, -1), 0, C_WHITE),
        ("LINEBEFORE",    (0, 0), (-1, -1), 3, _THEME["primary"]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    t.spaceBefore = 5 * mm
    t.spaceAfter  = 3 * mm
    return t


def _data_table(data: list[list], col_widths=None) -> Table:
    """Tableau 2 colonnes paramètre/valeur avec style professionnel."""
    if col_widths is None:
        col_widths = [CONTENT_W * 0.55, CONTENT_W * 0.45]
    t = Table(data, colWidths=col_widths)
    cmds = [
        ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",     (0, 0), (-1,  0), C_WHITE),
        ("BACKGROUND",    (0, 0), (-1,  0), _THEME["secondary"]),
        ("ALIGN",         (1, 0), (1,  -1), "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
    t.setStyle(TableStyle(cmds))
    t.spaceAfter = 4 * mm
    return t


def _kpi_table(kpis: list[tuple[str, str, str]]) -> Table:
    """
    Tableau de KPIs en grille 2 colonnes.
    kpis = [(valeur, label, couleur), ...]
    """
    cells = []
    row = []
    for i, (val, label, color) in enumerate(kpis):
        v_para = Paragraph(
            val,
            ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=18,
                           textColor=HexColor(color), alignment=TA_CENTER),
        )
        l_para = Paragraph(
            label,
            ParagraphStyle("kl", fontName="Helvetica", fontSize=8,
                           textColor=C_TEXT_SEC, alignment=TA_CENTER),
        )
        cell = Table([[v_para], [l_para]])
        cell.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        row.append(cell)
        if len(row) == 2:
            cells.append(row)
            row = []
    if row:
        while len(row) < 2:
            row.append(Spacer(1, 1))
        cells.append(row)

    col_w = CONTENT_W / 2
    t = Table(cells, colWidths=[col_w, col_w])
    cmds = [
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("BACKGROUND",    (0, 0), (-1, -1), C_SURFACE),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]
    t.setStyle(TableStyle(cmds))
    t.spaceAfter = 5 * mm
    return t


# ── Page callbacks ────────────────────────────────────────────────────────────

def _draw_solar_grid(canvas, x, y, w, h, color, alpha=0.06):
    """Dessine une grille de panneaux solaires stylisée (fond décoratif)."""
    canvas.saveState()
    canvas.setFillColor(color)
    cell = 12 * mm
    cols = int(w / cell) + 1
    rows = int(h / cell) + 1
    canvas.setFillAlpha(alpha)
    for row in range(rows):
        for col in range(cols):
            cx = x + col * cell
            cy = y + row * cell
            # Panel rectangle with slight rounding effect (inner rect)
            canvas.rect(cx + 1, cy + 1, cell - 2, cell - 2, fill=1, stroke=0)
            # Separator lines (darker)
            canvas.setFillAlpha(alpha * 0.5)
            canvas.rect(cx + 1, cy + cell // 2, cell - 2, 0.5, fill=1, stroke=0)
            canvas.rect(cx + cell // 2, cy + 1, 0.5, cell - 2, fill=1, stroke=0)
            canvas.setFillAlpha(alpha)
    canvas.restoreState()


def _draw_kpi_badge(canvas, x, y, w, h, value, label, color):
    """Dessine un badge KPI rectangulaire arrondi sur le canvas."""
    canvas.saveState()
    # Background card
    canvas.setFillColor(HexColor("#1E3A5F"))
    canvas.roundRect(x, y, w, h, 3 * mm, fill=1, stroke=0)
    # Accent top bar
    canvas.setFillColor(color)
    canvas.roundRect(x, y + h - 2 * mm, w, 2 * mm, 1 * mm, fill=1, stroke=0)
    # Value (may have actual newline for unit)
    lines = value.split("\n")
    canvas.setFillColor(color)
    if len(lines) >= 2:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawCentredString(x + w / 2, y + h * 0.52, lines[0])
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#94A3B8"))
        canvas.drawCentredString(x + w / 2, y + h * 0.37, lines[1])
    else:
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawCentredString(x + w / 2, y + h * 0.42, lines[0])
    # Label
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(HexColor("#64748B"))
    canvas.drawCentredString(x + w / 2, y + h * 0.18, label)
    canvas.restoreState()


def _cover_callback(canvas, doc):
    """Dessine la page de garde complète directement sur le canvas."""
    canvas.saveState()
    W, H = PAGE_W, PAGE_H

    # ── Fond principal (dégradé simulé avec rectangles) ──────────────────────
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Bande supérieure légèrement différente
    canvas.setFillColor(HexColor("#0A1628"))
    canvas.rect(0, H * 0.55, W, H * 0.45, fill=1, stroke=0)

    # ── Grille de panneaux (décor) ────────────────────────────────────────────
    _draw_solar_grid(canvas, 0, H * 0.28, W, H * 0.45, C_PRIMARY, alpha=0.055)

    # ── Bande header bleue foncée ─────────────────────────────────────────────
    canvas.setFillColor(_THEME["secondary"])
    canvas.rect(0, H - 20 * mm, W, 20 * mm, fill=1, stroke=0)

    # ── Ligne accent amber sous le header ────────────────────────────────────
    canvas.setFillColor(C_AMBER)
    canvas.rect(0, H - 20 * mm - 1.5 * mm, W, 1.5 * mm, fill=1, stroke=0)

    # ── Barre verticale gauche ────────────────────────────────────────────────
    canvas.setFillColor(_THEME["primary"])
    canvas.rect(0, 0, 6 * mm, H, fill=1, stroke=0)

    # ── Logo dans le header ───────────────────────────────────────────────────
    logo = getattr(doc, "_logo_path", None)
    logo_end_x = MARGIN + 6 * mm   # after sidebar
    if logo and os.path.isfile(logo):
        try:
            logo_size = 14 * mm
            canvas.drawImage(
                logo,
                logo_end_x + 2 * mm, H - 18 * mm,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True, mask="auto",
            )
            logo_end_x += logo_size + 4 * mm
        except Exception:
            pass

    # ── Nom entreprise dans le header ─────────────────────────────────────────
    company = getattr(doc, "_company_name", "SolarIntel")
    canvas.setFont("Helvetica-Bold", 13)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(logo_end_x, H - 11 * mm, company)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#93C5FD"))
    canvas.drawString(logo_end_x, H - 17 * mm, "Dimensionnement Photovoltaïque · Intelligence Solaire")

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#64748B"))
    canvas.drawRightString(W - 8 * mm, H - 11 * mm, "CONFIDENTIEL")
    canvas.drawRightString(W - 8 * mm, H - 17 * mm, date.today().strftime("%d/%m/%Y"))

    # ── Zone titre (milieu haut) ──────────────────────────────────────────────
    title_y = H * 0.68
    title = getattr(doc, "_report_title", "Rapport de Dimensionnement Solaire")
    if len(title) > 38:
        mid = title[:38].rfind(" ")
        _draw_centered_text(canvas, title[:mid],  "Helvetica-Bold", 28, C_WHITE, W, title_y)
        _draw_centered_text(canvas, title[mid+1:], "Helvetica-Bold", 22, C_WHITE, W, title_y - 18 * mm)
    else:
        _draw_centered_text(canvas, title, "Helvetica-Bold", 28, C_WHITE, W, title_y)

    # Sous-titre
    _draw_centered_text(canvas, "Rapport d'étude — Simulation pvlib & Analyse économique",
                        "Helvetica", 10, HexColor("#93C5FD"), W, title_y - 20 * mm)

    # ── Ligne séparatrice dorée ────────────────────────────────────────────────
    line_y = title_y - 26 * mm
    canvas.setStrokeColor(C_AMBER)
    canvas.setLineWidth(1)
    canvas.line(MARGIN + 6 * mm, line_y, W / 2 - 15 * mm, line_y)
    canvas.line(W / 2 + 15 * mm, line_y, W - MARGIN, line_y)
    # Sun icon center
    canvas.setFont("Helvetica-Bold", 16)
    canvas.setFillColor(C_AMBER)
    canvas.drawCentredString(W / 2, line_y - 4, "☀")

    # ── Système info (amber) ──────────────────────────────────────────────────
    sys_info = getattr(doc, "_sys_info", "")
    if sys_info:
        _draw_centered_text(canvas, sys_info, "Helvetica-Bold", 13, C_AMBER, W, line_y - 16 * mm)

    # ── 4 KPI badges ─────────────────────────────────────────────────────────
    kpi_data = getattr(doc, "_cover_kpis", [])
    if kpi_data:
        badge_w = (W - MARGIN * 2 - 6 * mm - 9 * mm) / 4
        badge_h = 18 * mm
        badge_y = H * 0.28 + 3 * mm
        badge_x = MARGIN + 6 * mm
        for i, (val, lbl, col) in enumerate(kpi_data):
            _draw_kpi_badge(canvas, badge_x + i * (badge_w + 3 * mm), badge_y,
                            badge_w, badge_h, val, lbl, HexColor(col))

    # ── Section client (fond légèrement différent) ────────────────────────────
    client_bg_y = 12 * mm
    client_bg_h = H * 0.28 - 12 * mm
    canvas.setFillColor(HexColor("#0D1B2E"))
    canvas.rect(6 * mm, client_bg_y, W - 6 * mm, client_bg_h, fill=1, stroke=0)

    x_info = MARGIN + 6 * mm
    y_base = H * 0.28 - 10 * mm

    def _info_line(label: str, value: str, y: float):
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(C_TEXT_LIGHT)
        canvas.drawString(x_info, y, label)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(x_info + 30 * mm, y, value)

    client_name = getattr(doc, "_client_name", "")
    location    = getattr(doc, "_location",    "")
    gen_date    = getattr(doc, "_gen_date",    date.today().isoformat())

    if client_name:
        _info_line("Client :",   client_name, y_base)
        y_base -= 8 * mm
    if location:
        _info_line("Site :",     location,    y_base)
        y_base -= 8 * mm
    _info_line("Établi le :",    gen_date,    y_base)

    # ── Pied de page ──────────────────────────────────────────────────────────
    canvas.setFillColor(_THEME["secondary"])
    canvas.rect(0, 0, W, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(C_AMBER)
    canvas.rect(0, 12 * mm - 1, W, 1, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(MARGIN + 6 * mm, 5 * mm, "Propulsé par TECH SUPPLY CONNECT  ·  pvlib  ·  CrewAI  ·  pvgis")
    canvas.drawRightString(W - 8 * mm, 5 * mm, "www.solarintel.io  ·  © 2026")

    canvas.restoreState()


def _draw_centered_text(canvas, text, font, size, color, page_w, y):
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    canvas.drawCentredString(page_w / 2, y, text)


def _content_callback(canvas, doc):
    """Header et footer pour les pages de contenu."""
    canvas.saveState()
    W, H = PAGE_W, PAGE_H

    # ── Header band (navy + amber bottom line) ────────────────────────────────
    canvas.setFillColor(_THEME["secondary"])
    canvas.rect(0, H - 16 * mm, W, 16 * mm, fill=1, stroke=0)

    canvas.setFillColor(C_AMBER)
    canvas.rect(0, H - 16 * mm, W, 1 * mm, fill=1, stroke=0)

    # Sidebar bleu sur toutes les pages
    canvas.setFillColor(_THEME["primary"])
    canvas.rect(0, 0, 4 * mm, H, fill=1, stroke=0)

    # Logo dans le header
    logo = getattr(doc, "_logo_path", None)
    logo_end_x = MARGIN + 4 * mm
    if logo and os.path.isfile(logo):
        try:
            canvas.drawImage(
                logo, logo_end_x + 1 * mm, H - 14.5 * mm,
                width=10 * mm, height=10 * mm,
                preserveAspectRatio=True, mask="auto",
            )
            logo_end_x += 12 * mm
        except Exception:
            pass

    # Nom société dans le header
    company = getattr(doc, "_company_name", "SolarIntel")
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(logo_end_x, H - 9 * mm, company)

    # Titre rapport dans le header (centre)
    r_title = getattr(doc, "_report_title", "")
    if r_title:
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(HexColor("#93C5FD"))
        canvas.drawCentredString(W / 2, H - 9 * mm, r_title)

    # Numéro de page (droite du header)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_AMBER)
    canvas.drawRightString(W - MARGIN, H - 9 * mm, f"{doc.page}")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_TEXT_LIGHT)
    canvas.drawRightString(W - MARGIN - 5 * mm, H - 9 * mm, "Page")

    # ── Footer ────────────────────────────────────────────────────────────────
    canvas.setFillColor(_THEME["secondary"])
    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(_THEME["primary"])
    canvas.rect(0, 10 * mm, W, 0.5 * mm, fill=1, stroke=0)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_TEXT_LIGHT)
    gen_date = getattr(doc, "_gen_date", date.today().isoformat())
    client   = getattr(doc, "_client_name", "")
    footer_l = f"Généré le {gen_date}"
    if client:
        footer_l += f"  ·  Client : {client}"
    canvas.drawString(MARGIN + 4 * mm, 3.5 * mm, footer_l)
    canvas.drawRightString(W - MARGIN, 3.5 * mm, f"{company}  ·  Confidentiel  ·  SolarIntel")

    canvas.restoreState()


# ── ReportGenerator ───────────────────────────────────────────────────────────

class ReportGenerator:
    """Génère un PDF professionnel SolarIntel v2."""

    def __init__(
        self,
        report: SolarReport,
        logo_path: str | Path | None = None,
        company_name: str | None = None,
        color_primary: str | None = None,
        color_secondary: str | None = None,
    ):
        self.report          = report
        self.logo_path       = str(logo_path) if logo_path else None
        self.company_name    = company_name or report.company_name
        self.color_primary   = HexColor(color_primary)   if color_primary   else C_PRIMARY
        self.color_secondary = HexColor(color_secondary) if color_secondary else C_PRIMARY_DARK

        # Auto-detect logo si non fourni
        if not self.logo_path:
            guesses = [
                Path(__file__).parent.parent.parent / "assets" / "logo_solarintel.png",
                Path(__file__).parent.parent.parent / "assets" / "logo.png",
            ]
            for g in guesses:
                if g.exists():
                    self.logo_path = str(g)
                    break

    def generate(self, output_path: str = "rapport_solarintel.pdf") -> str:
        # Override module-level theme so all helpers pick up user colors
        global _THEME
        _THEME["primary"]   = self.color_primary
        _THEME["secondary"] = self.color_secondary

        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=14 * mm + MARGIN,
            bottomMargin=12 * mm + MARGIN,
        )

        # Métadonnées sur le doc (accessibles dans les callbacks)
        r = self.report
        doc._logo_path    = self.logo_path
        doc._company_name = self.company_name
        doc._report_title = r.report_title
        doc._gen_date     = r.generation_date.strftime("%d/%m/%Y")
        doc._client_name  = getattr(r, "client_name", "")
        doc._location     = r.system.location_name
        doc._sys_info     = (
            f"{r.system.panel_count} panneaux  ·  {r.system.total_power_kwc:.1f} kWc  ·  "
            f"{_fmt(r.simulation.annual_production_kwh)} kWh/an"
            if r.system.panel_count > 0 else ""
        )
        # KPI badges on cover (value\nunit, label, hex_color)
        doc._cover_kpis = [
            (f"{_fmt(r.simulation.annual_production_kwh)}\nkWh/an", "Production annuelle", "#0EA5E9"),
            (f"{r.economics.payback_years:.1f} ans\n",               "Retour investissement", "#F59E0B"),
            (f"{_fmt(r.economics.annual_savings_xof)}\nXOF/an",      "Économie année 1",    "#22C55E"),
            (f"{_fmt(r.economics.lcoe_xof_kwh, 1)}\nXOF/kWh",        "LCOE 25 ans",         "#A78BFA"),
        ] if r.system.panel_count > 0 else []

        # ── Frames ───────────────────────────────────────────────────────────
        cover_frame = Frame(
            0, 0, PAGE_W, PAGE_H,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
            id="cover",
        )
        content_frame = Frame(
            MARGIN + 4 * mm,
            10 * mm + MARGIN,
            CONTENT_W - 4 * mm,
            PAGE_H - 16 * mm - 10 * mm - 2 * MARGIN,
            id="content",
        )

        doc.addPageTemplates([
            PageTemplate(id="cover",   frames=[cover_frame],   onPage=_cover_callback),
            PageTemplate(id="content", frames=[content_frame], onPage=_content_callback),
        ])

        # ── Story ─────────────────────────────────────────────────────────────
        story: list = []
        self._add_cover(story)
        self._add_executive_summary(story)
        self._add_system_config(story)
        self._add_simulation(story)
        self._add_economics(story)
        if getattr(r, "appliances", None):
            self._add_energy_balance(story)
        self._add_equipment(story)
        self._add_qa(story)
        self._add_appendix(story)

        doc.build(story)
        return os.path.abspath(output_path)

    # ── Cover ─────────────────────────────────────────────────────────────────

    def _add_cover(self, story: list) -> None:
        """Tout est dessiné dans _cover_callback — on fait juste passer au template suivant."""
        story.append(NextPageTemplate("content"))
        story.append(PageBreak())

    # ── Section 1 : Résumé exécutif ──────────────────────────────────────────

    def _add_executive_summary(self, story: list) -> None:
        r = self.report
        story.append(_section_header("1. Résumé exécutif"))

        body_style = ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=C_TEXT, leading=15, spaceAfter=3 * mm,
            alignment=TA_JUSTIFY,
        )

        if r.executive_summary:
            for line in r.executive_summary.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 3 * mm))
        else:
            summary = (
                f"Ce rapport présente le dimensionnement d'une installation photovoltaïque "
                f"de <b>{_fmt(r.system.total_power_kwc, 1)} kWc</b> "
                f"({r.system.panel_count} panneaux {r.system.panel_brand} {r.system.panel_power_wc} Wc) "
                f"sur le site de <b>{r.system.location_name}</b>. "
                f"La simulation pvlib estime une production annuelle de "
                f"<b>{_fmt(r.simulation.annual_production_kwh)} kWh</b>. "
                f"L'analyse économique projette un retour sur investissement de "
                f"<b>{r.economics.payback_years:.1f} ans</b> et un LCOE de "
                f"<b>{_fmt(r.economics.lcoe_xof_kwh, 1)} {r.economics.currency}/kWh</b>."
            )
            story.append(Paragraph(summary, body_style))

        # KPIs
        kpis = [
            (_fmt(r.simulation.annual_production_kwh) + " kWh/an", "Production annuelle",  "#0EA5E9"),
            (f"{r.simulation.performance_ratio:.1%}",               "Ratio de performance", "#22C55E"),
            (f"{r.economics.payback_years:.1f} ans",                "Retour investissement","#F59E0B"),
            (_fmt(r.economics.lcoe_xof_kwh, 1) + " XOF/kWh",       "LCOE",                 "#8B5CF6"),
        ]
        story.append(_kpi_table(kpis))

    # ── Section 2 : Configuration système ────────────────────────────────────

    def _add_system_config(self, story: list) -> None:
        sys = self.report.system
        story.append(_section_header("2. Configuration système"))

        story.append(_subsection_header("2.1  Spécifications panneaux"))
        eff_pct = sys.panel_efficiency * 100 if sys.panel_efficiency < 1 else sys.panel_efficiency
        story.append(_data_table([
            ["Paramètre",           "Valeur"],
            ["Marque",              sys.panel_brand],
            ["Modèle",              sys.panel_model],
            ["Puissance unitaire",  f"{sys.panel_power_wc} Wc"],
            ["Efficacité",          f"{eff_pct:.1f} %"],
            ["Nombre de panneaux",  f"{sys.panel_count}"],
            ["Puissance totale",    f"{sys.total_power_kwc:.2f} kWc"],
        ]))

        story.append(_subsection_header("2.2  Localisation & orientation"))
        story.append(_data_table([
            ["Paramètre",   "Valeur"],
            ["Site",        sys.location_name],
            ["Latitude",    f"{sys.latitude:.4f}°"],
            ["Longitude",   f"{sys.longitude:.4f}°"],
            ["Altitude",    f"{sys.altitude:.0f} m"],
            ["Azimut",      f"{sys.orientation_azimuth:.0f}°  (180° = Plein sud)"],
            ["Inclinaison", f"{sys.tilt:.0f}°"],
        ]))

    # ── Section 3 : Simulation pvlib ──────────────────────────────────────────

    def _add_simulation(self, story: list) -> None:
        sim = self.report.simulation
        story.append(_section_header("3. Simulation photovoltaïque"))

        story.append(_subsection_header("3.1  Indicateurs clés de performance"))
        story.append(_data_table([
            ["Indicateur",           "Valeur"],
            ["Production annuelle",  f"{_fmt(sim.annual_production_kwh)} kWh"],
            ["Rendement spécifique", f"{_fmt(sim.specific_yield_kwh_kwc)} kWh/kWc"],
            ["Performance Ratio",   f"{sim.performance_ratio:.1%}"],
        ]))

        story.append(_subsection_header("3.2  Production mensuelle estimée"))
        chart = build_monthly_production_chart(sim.monthly_production_kwh)
        story.append(KeepTogether([chart, Spacer(1, 3 * mm)]))

        story.append(_subsection_header("3.3  Bilan des pertes système"))
        story.append(_data_table([
            ["Source de perte",        "Valeur (%)"],
            ["Salissure (soiling)",    f"{sim.soiling_loss_pct:.1f}"],
            ["Mismatch",               f"{sim.mismatch_loss_pct:.1f}"],
            ["Câblage DC + AC",        f"{sim.wiring_loss_pct:.1f}"],
            ["Disponibilité système",  f"{sim.availability_loss_pct:.1f}"],
            ["Dégradation thermique",  f"{sim.temperature_loss_pct:.1f}"],
            ["Total pertes estimées",  f"{sim.total_losses_pct:.1f}"],
        ]))

    # ── Section 4 : Analyse économique ───────────────────────────────────────

    def _add_economics(self, story: list) -> None:
        eco = self.report.economics
        cur = eco.currency
        story.append(_section_header("4. Analyse économique"))

        story.append(_subsection_header("4.1  Indicateurs financiers"))
        story.append(_data_table([
            ["Indicateur",             "Valeur"],
            ["CAPEX total",            f"{_fmt(eco.total_cost_xof)} {cur}"],
            ["Coût par kWc installé",  f"{_fmt(eco.cost_per_kwc_xof)} {cur}/kWc"],
            ["Économie annuelle (an 1)",f"{_fmt(eco.annual_savings_xof)} {cur}/an"],
            ["LCOE (25 ans)",          f"{_fmt(eco.lcoe_xof_kwh, 1)} {cur}/kWh"],
            ["ROI global",             f"{eco.roi_pct:.1f} %"],
            ["Temps de retour",        f"{eco.payback_years:.1f} ans"],
            ["VAN 25 ans",             f"{_fmt(eco.npv_xof)} {cur}"],
        ]))

        if any(v != 0 for v in eco.cashflow_cumulative):
            story.append(_subsection_header("4.2  Flux de trésorerie cumulé (25 ans)"))
            chart = build_cashflow_chart(eco.cashflow_cumulative)
            story.append(KeepTogether([chart, Spacer(1, 3 * mm)]))

    # ── Section 5 : Bilan énergétique ────────────────────────────────────────

    def _add_energy_balance(self, story: list) -> None:
        r = self.report
        appliances = getattr(r, "appliances", [])
        if not appliances:
            return

        story.append(_section_header("5. Bilan énergétique"))
        story.append(_subsection_header("5.1  Tableau des consommations"))

        col_w = [CONTENT_W * 0.30, CONTENT_W * 0.08, CONTENT_W * 0.10,
                 CONTENT_W * 0.12, CONTENT_W * 0.12, CONTENT_W * 0.14, CONTENT_W * 0.14]

        rows = [["Appareil", "Qté", "W", "h/Jour", "h/Nuit", "kWh Jour", "kWh Nuit"]]

        total_day = total_night = 0.0
        for a in appliances:
            kwh_d = a.get("qty", 1) * a.get("power", 0) * a.get("hoursDay",   0) / 1000
            kwh_n = a.get("qty", 1) * a.get("power", 0) * a.get("hoursNight", 0) / 1000
            total_day   += kwh_d
            total_night += kwh_n
            rows.append([
                a.get("name", "—"),
                str(a.get("qty", 1)),
                f"{a.get('power', 0):.0f}",
                f"{a.get('hoursDay',   0):.1f}",
                f"{a.get('hoursNight', 0):.1f}",
                f"{kwh_d:.2f}",
                f"{kwh_n:.2f}",
            ])

        rows.append(["Total / jour", "", "", "", "",
                     f"{total_day:.2f}", f"{total_night:.2f}"])

        t = Table(rows, colWidths=col_w)
        n = len(rows)
        cmds = [
            ("FONTNAME",      (0,  0), (-1,  0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,  1), (-1, -2),  "Helvetica"),
            ("FONTNAME",      (0, -1), (-1, -1),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,  0), (-1, -1),  8),
            ("TEXTCOLOR",     (0,  0), (-1,  0),  C_WHITE),
            ("BACKGROUND",    (0,  0), (-1,  0),  _THEME["secondary"]),
            ("BACKGROUND",    (0, -1), (-1, -1),  HexColor("#FEF3C7")),
            ("ALIGN",         (1,  0), (-1, -1),  "RIGHT"),
            ("ALIGN",         (0,  0), (0,  -1),  "LEFT"),
            ("GRID",          (0,  0), (-1, -1),  0.4, C_BORDER),
            ("TOPPADDING",    (0,  0), (-1, -1),  3),
            ("BOTTOMPADDING", (0,  0), (-1, -1),  3),
            ("LEFTPADDING",   (0,  0), (-1, -1),  5),
            ("RIGHTPADDING",  (0,  0), (-1, -1),  5),
        ]
        for i in range(1, n - 1):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
        t.setStyle(TableStyle(cmds))
        t.spaceAfter = 4 * mm
        story.append(t)

        # Totaux
        body_sm = ParagraphStyle("bsm", fontName="Helvetica", fontSize=9,
                                 textColor=C_TEXT_SEC, spaceAfter=1 * mm)
        story.append(Paragraph(
            f"Consommation journalière totale : "
            f"<b>{total_day + total_night:.2f} kWh/jour</b>  "
            f"({total_day:.2f} kWh jour + {total_night:.2f} kWh nuit)",
            body_sm,
        ))
        monthly = (total_day + total_night) * 30
        story.append(Paragraph(
            f"Consommation mensuelle estimée : <b>{monthly:.0f} kWh/mois</b>  "
            f"· Annuelle : <b>{monthly * 12:.0f} kWh/an</b>",
            body_sm,
        ))

    # ── Section 6 : Équipements ───────────────────────────────────────────────

    def _add_equipment(self, story: list) -> None:
        r = self.report
        equip = getattr(r, "equipment", None)
        if not equip:
            return

        story.append(_section_header("6. Équipements du système"))

        inv  = equip.get("inverter", {})
        bat  = equip.get("battery",  {})
        capex = equip.get("capex",   {})

        if inv:
            story.append(_subsection_header("6.1  Onduleur"))
            inv_rows = [["Paramètre", "Valeur"]]
            for k, v in inv.items():
                inv_rows.append([k, str(v)])
            story.append(_data_table(inv_rows))

        if bat:
            story.append(_subsection_header("6.2  Stockage batterie"))
            bat_rows = [["Paramètre", "Valeur"]]
            for k, v in bat.items():
                bat_rows.append([k, str(v)])
            story.append(_data_table(bat_rows))

        if capex:
            story.append(_subsection_header("6.3  Détail CAPEX"))
            capex_rows = [["Poste", "Montant (XOF)"]]
            for k, v in capex.items():
                capex_rows.append([k, _fmt(float(v))])
            story.append(_data_table(capex_rows))

    # ── Section 7 : QA ────────────────────────────────────────────────────────

    def _add_qa(self, story: list) -> None:
        qa = self.report.qa
        n_section = 7 if getattr(self.report, "appliances", None) else 6
        story.append(_section_header(f"{n_section}. Rapport Qualité & Validation"))

        if qa.validations:
            story.append(_subsection_header(f"{n_section}.1  Matrice de validation"))
            story.append(self._build_qa_table(
                [["Code", "Critère", "Statut", "Détail"]] +
                [[v.code, v.label, v.status, v.detail] for v in qa.validations]
            ))

        if qa.edge_cases:
            story.append(_subsection_header(f"{n_section}.2  Cas limites"))
            story.append(self._build_qa_table(
                [["Code", "Critère", "Statut", "Détail"]] +
                [[e.code, e.label, e.status, e.detail] for e in qa.edge_cases]
            ))

        verdict_color = C_GREEN if qa.verdict == "PASS" else C_RED
        verdict_style = ParagraphStyle(
            "verd", fontName="Helvetica-Bold", fontSize=16,
            textColor=verdict_color, alignment=TA_CENTER, spaceAfter=3 * mm,
        )
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(f"Verdict global : {qa.verdict}", verdict_style))
        if qa.notes:
            body_sm = ParagraphStyle("bsm2", fontName="Helvetica", fontSize=9,
                                     textColor=C_TEXT_SEC)
            story.append(Paragraph(qa.notes, body_sm))

    # ── Section Annexes ───────────────────────────────────────────────────────

    def _add_appendix(self, story: list) -> None:
        story.append(PageBreak())
        n_section = 8 if getattr(self.report, "appliances", None) else 7
        story.append(_section_header(f"{n_section}. Annexes"))

        body_sm = ParagraphStyle("bsm3", fontName="Helvetica", fontSize=8,
                                 textColor=C_TEXT_SEC, spaceAfter=1 * mm, leading=11)
        mono    = ParagraphStyle("mono", fontName="Courier", fontSize=8,
                                 textColor=C_TEXT, spaceAfter=1 * mm)

        story.append(_subsection_header("Modules pvlib utilisés"))
        for mod in PVLIB_MODULES:
            story.append(Paragraph(f"• <font face='Courier'>{mod}</font>", body_sm))

        story.append(_subsection_header("Constantes économiques"))
        for k, v in ECONOMIC_DEFAULTS.items():
            story.append(Paragraph(f"• <b>{k}</b> : {v}", body_sm))

        story.append(_subsection_header("Méthodologie"))
        story.append(Paragraph(
            "Simulation pvlib (TMY PVGIS) · ModelChain · Pertes système (salissure, "
            "mismatch, câblage, température) · Économie SENELEC · Dégradation 0.5 %/an "
            "· Durée de vie 25 ans · LCOE = CAPEX / Σ(Production_i × (1-dég)^i).",
            body_sm,
        ))

        if self.report.raw_crew_output:
            story.append(PageBreak())
            story.append(_subsection_header("Recommandations IA (CrewAI / Ollama)"))
            raw = self.report.raw_crew_output
            if len(raw) > 5000:
                raw = raw[:5000] + "\n\n[... tronqué ...]"
            for line in raw.split("\n"):
                line = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                story.append(Paragraph(line or "&nbsp;", mono))

    # ── QA table helper ───────────────────────────────────────────────────────

    def _build_qa_table(self, data: list[list[str]]) -> Table:
        avail = CONTENT_W
        col_w = [18 * mm, avail - 18 * mm - 22 * mm - 60 * mm, 22 * mm, 60 * mm]
        t = Table(data, colWidths=col_w)
        cmds = [
            ("FONTNAME",      (0, 0), (-1,  0), "Helvetica-Bold"),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("TEXTCOLOR",     (0, 0), (-1,  0), C_WHITE),
            ("BACKGROUND",    (0, 0), (-1,  0), _THEME["secondary"]),
            ("ALIGN",         (2, 0), (2,  -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ]
        for i in range(1, len(data)):
            status = data[i][2] if len(data[i]) > 2 else ""
            color  = (C_GREEN if status == "PASS"
                      else C_RED if status == "FAIL"
                      else HexColor("#F97316") if status == "WARNING"
                      else C_TEXT_SEC)
            cmds.append(("TEXTCOLOR", (2, i), (2, i), color))
            cmds.append(("FONTNAME",  (2, i), (2, i), "Helvetica-Bold"))
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
        t.setStyle(TableStyle(cmds))
        t.spaceAfter = 4 * mm
        return t
