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
    PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image,
)

from solarintel.reports.models import SolarReport
from solarintel.reports.theme import ReportTheme
from solarintel.reports.charts import (
    build_monthly_production_chart, build_cashflow_chart,
    build_load_profile_chart, build_monthly_comparison_chart,
    build_senelec_billing_chart, build_usage_category_chart,
)
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
    canvas.setFillColor(_THEME["primary"])
    canvas.drawString(logo_end_x, H - 17 * mm, "Dimensionnement Photovoltaïque · Intelligence Solaire")

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_THEME["primary"])
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
    canvas.setFillColor(_THEME["primary"])
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
        canvas.setFillColor(_THEME["primary"])
        canvas.drawCentredString(W / 2, H - 9 * mm, r_title)

    # Numéro de page (droite du header)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_AMBER)
    canvas.drawRightString(W - MARGIN, H - 9 * mm, f"{doc.page}")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_THEME["primary"])
    canvas.drawRightString(W - MARGIN - 5 * mm, H - 9 * mm, "Page")

    # ── Footer ────────────────────────────────────────────────────────────────
    canvas.setFillColor(_THEME["secondary"])
    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(_THEME["primary"])
    canvas.rect(0, 10 * mm, W, 0.5 * mm, fill=1, stroke=0)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_THEME["primary"])
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

        sec = 5  # numéro de la prochaine section (dynamique)
        if getattr(r, "appliances", None):
            self._add_energy_balance(story, sec)
            sec += 1
        if getattr(r, "senelec_analysis", None):
            self._add_senelec_analysis(story, sec)
            sec += 1
        if getattr(r, "calepinage", None):
            self._add_calepinage(story, sec)
            sec += 1
        self._add_equipment(story, sec);  sec += 1
        self._add_qa(story, sec);         sec += 1
        self._add_appendix(story, sec)

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

    def _add_energy_balance(self, story: list, sec: int = 5) -> None:
        r = self.report
        appliances = getattr(r, "appliances", [])
        if not appliances:
            return

        story.append(_section_header(f"{sec}. Bilan énergétique"))
        story.append(_subsection_header(f"{sec}.1  Tableau des consommations"))

        col_w = [CONTENT_W * 0.26, CONTENT_W * 0.07, CONTENT_W * 0.09,
                 CONTENT_W * 0.09, CONTENT_W * 0.09, CONTENT_W * 0.08,
                 CONTENT_W * 0.14, CONTENT_W * 0.10, CONTENT_W * 0.08]

        rows = [["Appareil", "Qté", "W", "h/Jour", "h/Nuit", "cos φ", "kWh/jour", "kVA", "kWh/mois"]]

        total_kwh = total_kva = 0.0
        for a in appliances:
            qty   = a.get("qty", 1)
            power = a.get("power", 0)
            hd    = a.get("hoursDay",   0)
            hn    = a.get("hoursNight", 0)
            cp    = a.get("cos_phi", 1.0) or 1.0
            kwh   = qty * power * (hd + hn) / 1000
            kva   = qty * power / (cp * 1000) if cp > 0 else 0
            total_kwh += kwh
            total_kva += kva
            rows.append([
                a.get("name", "—"),
                str(qty),
                f"{power:.0f}",
                f"{hd:.1f}",
                f"{hn:.1f}",
                f"{cp:.2f}",
                f"{kwh:.2f}",
                f"{kva:.2f}",
                f"{kwh * 30:.1f}",
            ])

        rows.append(["Total / jour", "", "", "", "", "",
                     f"{total_kwh:.2f}", f"{total_kva:.2f}", f"{total_kwh * 30:.1f}"])

        t = Table(rows, colWidths=col_w)
        n = len(rows)
        cmds = [
            ("FONTNAME",      (0,  0), (-1,  0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,  1), (-1, -2),  "Helvetica"),
            ("FONTNAME",      (0, -1), (-1, -1),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,  0), (-1, -1),  7.5),
            ("TEXTCOLOR",     (0,  0), (-1,  0),  C_WHITE),
            ("BACKGROUND",    (0,  0), (-1,  0),  _THEME["secondary"]),
            ("BACKGROUND",    (0, -1), (-1, -1),  HexColor("#FEF3C7")),
            ("TEXTCOLOR",     (5,  1), (5,  -1),  HexColor("#A78BFA")),  # cos phi col purple
            ("TEXTCOLOR",     (7,  1), (7,  -1),  HexColor("#A78BFA")),  # kVA col purple
            ("ALIGN",         (1,  0), (-1, -1),  "RIGHT"),
            ("ALIGN",         (0,  0), (0,  -1),  "LEFT"),
            ("GRID",          (0,  0), (-1, -1),  0.4, C_BORDER),
            ("TOPPADDING",    (0,  0), (-1, -1),  3),
            ("BOTTOMPADDING", (0,  0), (-1, -1),  3),
            ("LEFTPADDING",   (0,  0), (-1, -1),  4),
            ("RIGHTPADDING",  (0,  0), (-1, -1),  4),
        ]
        for i in range(1, n - 1):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
        t.setStyle(TableStyle(cmds))
        t.spaceAfter = 4 * mm
        story.append(t)

        # Totaux + PF site
        body_sm = ParagraphStyle("bsm", fontName="Helvetica", fontSize=9,
                                 textColor=C_TEXT_SEC, spaceAfter=1 * mm)
        total_active_peak = sum(a.get("qty", 1) * a.get("power", 0) for a in appliances)
        total_app_peak    = sum(
            a.get("qty", 1) * a.get("power", 0) / (a.get("cos_phi", 1.0) or 1.0)
            for a in appliances
        )
        site_pf = total_active_peak / total_app_peak if total_app_peak > 0 else 1.0
        monthly = total_kwh * 30
        story.append(Paragraph(
            f"Consommation journalière totale : "
            f"<b>{total_kwh:.2f} kWh/jour</b>  ·  "
            f"Puissance apparente crête : <b>{total_kva:.2f} kVA</b>  ·  "
            f"FP moyen site : <b>{site_pf:.2f}</b>",
            body_sm,
        ))
        story.append(Paragraph(
            f"Consommation mensuelle estimée : <b>{monthly:.0f} kWh/mois</b>  "
            f"· Annuelle : <b>{monthly * 12:.0f} kWh/an</b>",
            body_sm,
        ))
        if site_pf < 0.80:
            warn_style = ParagraphStyle(
                "warn", fontName="Helvetica-Bold", fontSize=9,
                textColor=HexColor("#F97316"), spaceAfter=2 * mm,
            )
            story.append(Paragraph(
                f"⚠ ATTENTION : FP moyen site = {site_pf:.2f} < 0,80 — l'onduleur doit être "
                f"sélectionné sur la base de {total_kva:.1f} kVA (puissance apparente) "
                f"et non sur les kW seuls. Un facteur de puissance faible entraîne une "
                f"surtension des câbles et un échauffement prématuré de l'onduleur.",
                warn_style,
            ))

        # ── 5.2 Tableau P / Q / S / cos φ ────────────────────────────────────
        story.append(_subsection_header(f"{sec}.2  Puissances actives, réactives et apparentes"))
        import math as _math
        pqs_rows = [["Appareil", "P (kW)", "Q (kVAR)", "S (kVA)", "cos φ"]]
        total_p = total_q = total_s = 0.0
        for a in appliances:
            qty  = a.get("qty", 1) or 1
            pw   = (a.get("power", 0) or 0) * qty
            cp   = a.get("cos_phi", 1.0) or 1.0
            p_kw = pw / 1000
            s_kva = p_kw / cp if cp > 0 else p_kw
            phi  = _math.acos(max(0.01, min(1.0, cp)))
            q_kvar = s_kva * _math.sin(phi)
            total_p += p_kw; total_q += q_kvar; total_s += s_kva
            pqs_rows.append([
                a.get("name", "—"),
                f"{p_kw:.3f}", f"{q_kvar:.3f}", f"{s_kva:.3f}", f"{cp:.2f}",
            ])
        pqs_rows.append(["Total site",
                         f"{total_p:.3f}", f"{total_q:.3f}", f"{total_s:.3f}",
                         f"{(total_p / total_s):.2f}" if total_s > 0 else "1.00"])
        col_p = [CONTENT_W * 0.38, CONTENT_W * 0.155, CONTENT_W * 0.155,
                 CONTENT_W * 0.155, CONTENT_W * 0.155]
        pqs_t = Table(pqs_rows, colWidths=col_p)
        n_pqs = len(pqs_rows)
        pqs_cmds = [
            ("FONTNAME",      (0,  0), (-1,  0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,  1), (-1, -2),  "Helvetica"),
            ("FONTNAME",      (0, -1), (-1, -1),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,  0), (-1, -1),  8),
            ("TEXTCOLOR",     (0,  0), (-1,  0),  C_WHITE),
            ("BACKGROUND",    (0,  0), (-1,  0),  _THEME["secondary"]),
            ("BACKGROUND",    (0, -1), (-1, -1),  HexColor("#EDE9FE")),
            ("TEXTCOLOR",     (3,  1), (3, -1),   HexColor("#7C3AED")),  # S col
            ("ALIGN",         (1,  0), (-1, -1),  "RIGHT"),
            ("ALIGN",         (0,  0), (0,  -1),  "LEFT"),
            ("GRID",          (0,  0), (-1, -1),  0.4, C_BORDER),
            ("TOPPADDING",    (0,  0), (-1, -1),  3),
            ("BOTTOMPADDING", (0,  0), (-1, -1),  3),
            ("LEFTPADDING",   (0,  0), (-1, -1),  5),
            ("RIGHTPADDING",  (0,  0), (-1, -1),  5),
        ]
        for i in range(1, n_pqs - 1):
            if i % 2 == 0:
                pqs_cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
        pqs_t.setStyle(TableStyle(pqs_cmds))
        pqs_t.spaceAfter = 4 * mm
        story.append(pqs_t)

        # KPI badges P / Q / S
        kpi_pqs = [
            (f"{total_p:.2f} kW",   "Puissance active totale",    "#0EA5E9"),
            (f"{total_q:.2f} kVAR", "Puissance réactive totale",  "#F59E0B"),
            (f"{total_s:.2f} kVA",  "Puissance apparente totale", "#7C3AED"),
            (f"{total_p/total_s:.2f}" if total_s > 0 else "1.00",
                                     "Facteur de puissance moyen", "#22C55E"),
        ]
        story.append(_kpi_table(kpi_pqs))

        # ── 5.3 Courbe de charge journalière ─────────────────────────────────
        story.append(_subsection_header(f"{sec}.3  Profil de charge journalier (0h-24h)"))
        load_chart = build_load_profile_chart(appliances)
        story.append(KeepTogether([load_chart, Spacer(1, 3 * mm)]))

        # ── 5.4 Histogramme consommation mensuelle ────────────────────────────
        story.append(_subsection_header(f"{sec}.4  Comparaison mensuelle Production / Consommation"))
        sim_obj = getattr(r, "simulation", None)
        monthly_prod = getattr(sim_obj, "monthly_production_kwh", []) if sim_obj else []
        monthly_cons = [(total_kwh * 365 / 12)] * 12
        cmp_chart = build_monthly_comparison_chart(monthly_prod, monthly_cons)
        story.append(KeepTogether([cmp_chart, Spacer(1, 3 * mm)]))

        # ── 5.5 Répartition par usage ─────────────────────────────────────────
        story.append(_subsection_header(f"{sec}.5  Répartition de la consommation par usage"))
        usage_chart = build_usage_category_chart(appliances)
        story.append(KeepTogether([usage_chart, Spacer(1, 3 * mm)]))

    # ── Section SENELEC ────────────────────────────────────────────────────────

    def _add_senelec_analysis(self, story: list, sec: int = 6) -> None:
        r = self.report
        sa = getattr(r, "senelec_analysis", None)
        if not sa:
            return

        story.append(PageBreak())
        story.append(_section_header(f"{sec}. Analyse tarifaire SENELEC & économies"))

        tariff = sa.get("tariff_code", "DPP")
        annual_saving = sa.get("annual_saving_xof", 0)
        monthly = sa.get("monthly", [])

        # KPIs principaux
        if monthly:
            avg_before = sum(m["before_xof"] for m in monthly) / 12
            avg_after  = sum(m["after_xof"]  for m in monthly) / 12
            avg_cov    = sum(m["coverage_pct"] for m in monthly) / 12
            kpi_s = [
                (_fmt(avg_before),   "Facture moy. avant (FCFA/mois)", "#EF4444"),
                (_fmt(avg_after),    "Facture moy. après (FCFA/mois)", "#0EA5E9"),
                (_fmt(annual_saving),"Économie annuelle (FCFA/an)",    "#22C55E"),
                (f"{avg_cov:.0f} %", "Taux couverture moyen",          "#F59E0B"),
            ]
            story.append(_kpi_table(kpi_s))

        # ── 6.1 Grille tarifaire identifiée ──────────────────────────────────
        story.append(_subsection_header(
            f"{sec}.1  Catégorie tarifaire : {tariff.replace('_WOYOFAL', ' (Woyofal)')}"
        ))
        from solarintel.config.senelec import (
            SENELEC_TRANCHES, SENELEC_WOYOFAL,
            TRANCHE_1_MAX, TRANCHE_2_MAX,
        )
        is_woy = "WOYOFAL" in tariff
        code   = tariff.replace("_WOYOFAL", "")
        src    = SENELEC_WOYOFAL if is_woy else SENELEC_TRANCHES
        key    = f"{code}_WOYOFAL" if is_woy else code
        t1, t2, t3 = src.get(key, SENELEC_TRANCHES.get("DPP", (91.17, 136.49, 159.36)))
        story.append(_data_table([
            ["Tranche",                       "Plage (kWh/mois)", "Tarif (FCFA/kWh)"],
            [f"T1 — Tranche 1",               f"0 – {TRANCHE_1_MAX}",    f"{t1:.2f}"],
            [f"T2 — Tranche 2",               f"{TRANCHE_1_MAX+1} – {TRANCHE_2_MAX}", f"{t2:.2f}"],
            [f"T3 — Tranche 3{'*' if is_woy else ''}", f"> {TRANCHE_2_MAX}",  f"{t3:.2f}"],
        ], col_widths=[CONTENT_W * 0.45, CONTENT_W * 0.30, CONTENT_W * 0.25]))

        # ── 6.2 Tableau mensuel avant / après ────────────────────────────────
        story.append(_subsection_header(f"{sec}.2  Facturation mensuelle AVANT / APRÈS solaire"))
        tbl_rows = [["Mois", "Conso.\n(kWh)", "Prod.\n(kWh)", "Net\n(kWh)",
                     "Facture avant\n(FCFA)", "Facture après\n(FCFA)",
                     "Économie\n(FCFA)", "Couv.\n(%)"]]
        for m in monthly:
            tbl_rows.append([
                m["month"],
                f"{m['cons_kwh']:.0f}",
                f"{m['prod_kwh']:.0f}",
                f"{m['net_kwh']:.0f}",
                _fmt(m["before_xof"]),
                _fmt(m["after_xof"]),
                _fmt(m["saving_xof"]),
                f"{m['coverage_pct']:.0f}%",
            ])
        tot_b = sum(m["before_xof"] for m in monthly)
        tot_a = sum(m["after_xof"]  for m in monthly)
        tbl_rows.append(["TOTAL", "", "", "",
                         _fmt(tot_b), _fmt(tot_a), _fmt(tot_b - tot_a), ""])

        col_s = [CONTENT_W * 0.08, CONTENT_W * 0.09, CONTENT_W * 0.09, CONTENT_W * 0.09,
                 CONTENT_W * 0.165, CONTENT_W * 0.155, CONTENT_W * 0.155, CONTENT_W * 0.075]
        t = Table(tbl_rows, colWidths=col_s)
        n = len(tbl_rows)
        cmds = [
            ("FONTNAME",      (0,  0), (-1,  0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,  1), (-1, -2),  "Helvetica"),
            ("FONTNAME",      (0, -1), (-1, -1),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,  0), (-1, -1),  7),
            ("TEXTCOLOR",     (0,  0), (-1,  0),  C_WHITE),
            ("BACKGROUND",    (0,  0), (-1,  0),  _THEME["secondary"]),
            ("BACKGROUND",    (0, -1), (-1, -1),  HexColor("#DCFCE7")),
            ("TEXTCOLOR",     (6,  1), (6, -1),   C_GREEN),
            ("ALIGN",         (1,  0), (-1, -1),  "RIGHT"),
            ("ALIGN",         (0,  0), (0,  -1),  "LEFT"),
            ("GRID",          (0,  0), (-1, -1),  0.4, C_BORDER),
            ("TOPPADDING",    (0,  0), (-1, -1),  2),
            ("BOTTOMPADDING", (0,  0), (-1, -1),  2),
            ("LEFTPADDING",   (0,  0), (-1, -1),  4),
            ("RIGHTPADDING",  (0,  0), (-1, -1),  4),
        ]
        for i in range(1, n - 1):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
        t.setStyle(TableStyle(cmds))
        t.spaceAfter = 4 * mm
        story.append(t)

        # ── 6.3 Graphique factures ────────────────────────────────────────────
        story.append(_subsection_header(f"{sec}.3  Factures mensuelles et économies"))
        bill_chart = build_senelec_billing_chart(
            sa.get("bill_before", []), sa.get("bill_after", [])
        )
        story.append(KeepTogether([bill_chart, Spacer(1, 3 * mm)]))

        # ── 6.4 Taux de couverture mensuel ────────────────────────────────────
        story.append(_subsection_header(f"{sec}.4  Taux de couverture mensuel (%)"))
        cov_rows = [["Mois"] + [m["month"] for m in monthly]]
        cov_rows.append(["Taux"] + [f"{m['coverage_pct']:.0f}%" for m in monthly])
        col_c = [CONTENT_W * 0.12] + [CONTENT_W * 0.073] * 12
        cov_t = Table(cov_rows, colWidths=col_c)
        cov_cmds = [
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 1), 8),
            ("TEXTCOLOR",  (0, 0), (-1, 0), C_WHITE),
            ("BACKGROUND", (0, 0), (-1, 0), _THEME["secondary"]),
            ("ALIGN",      (0, 0), (-1, 1), "CENTER"),
            ("GRID",       (0, 0), (-1, 1), 0.4, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, 1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 1), 4),
        ]
        for i, m in enumerate(monthly, start=1):
            cov = m["coverage_pct"]
            color = (C_GREEN if cov >= 80 else
                     HexColor("#F59E0B") if cov >= 50 else C_RED)
            cov_cmds.append(("TEXTCOLOR", (i, 1), (i, 1), color))
        cov_t.setStyle(TableStyle(cov_cmds))
        cov_t.spaceAfter = 4 * mm
        story.append(cov_t)

    # ── Section Calepinage ────────────────────────────────────────────────────

    def _add_calepinage(self, story: list, sec: int = 7) -> None:
        r = self.report
        cal = getattr(r, "calepinage", None)
        if not cal:
            return

        story.append(PageBreak())
        story.append(_section_header(f"{sec}. Calepinage & plan d'implantation"))

        # ── Capture satellite ─────────────────────────────────────────────────
        map_img_path = cal.get("map_img_path") if cal else None
        if not map_img_path and cal:
            map_img_path = cal.get("map_img_path")

        if map_img_path:
            story.append(_subsection_header(f"{sec}.0  Vue satellite — panneaux positionnés"))
            try:
                img = Image(map_img_path, width=CONTENT_W, height=CONTENT_W * 0.55,
                            kind="proportional")
                img.hAlign = "CENTER"
                story.append(img)
                body_cap = ParagraphStyle(
                    "cap", fontName="Helvetica", fontSize=8,
                    textColor=C_TEXT_SEC, alignment=1, spaceAfter=4 * mm,
                )
                story.append(Paragraph(
                    f"Capture ArcGIS — {cal.get('panel_count', '?')} panneaux "
                    f"sur {cal.get('polygon_area_m2', '?')} m²  "
                    f"· {cal.get('latitude', 0):.5f}°N, {cal.get('longitude', 0):.5f}°E",
                    body_cap,
                ))
            except Exception:
                pass  # image invalide → on saute silencieusement

        story.append(_subsection_header(f"{sec}.1  Surfaces et disposition"))
        story.append(_data_table([
            ["Paramètre",                    "Valeur"],
            ["Surface totale zone tracée",   f"{cal.get('polygon_area_m2', 0):.1f} m²"],
            ["Surface nette panneaux",       f"{cal.get('used_area_m2', 0):.1f} m²"],
            ["Surface libre / obstacles",    f"{cal.get('free_area_m2', 0):.1f} m²"],
            ["Taux d'occupation",            f"{cal.get('coverage_pct', 0):.1f} %"],
        ]))

        story.append(_subsection_header(f"{sec}.2  Disposition des panneaux"))
        story.append(_data_table([
            ["Paramètre",                   "Valeur"],
            ["Nombre de panneaux",          f"{cal.get('panel_count', 0)}"],
            ["Dimensions panneau (L×H)",    cal.get("panel_dims", "—")],
            ["Orientation",                 cal.get("orientation", "Portrait")],
            ["Espacement horizontal",       f"{cal.get('spacing_h_cm', 2):.0f} cm"],
            ["Espacement vertical",         f"{cal.get('spacing_v_cm', 5):.0f} cm"],
            ["Rangées estimées",            f"{cal.get('est_rows', '—')}"],
            ["Panneaux / rangée",           f"{cal.get('est_cols', '—')}"],
        ]))

        story.append(_subsection_header(f"{sec}.3  Orientation & anti-ombrage"))
        story.append(_data_table([
            ["Paramètre",                      "Valeur"],
            ["Inclinaison (tilt)",              f"{cal.get('tilt_deg', 15):.1f}°"],
            ["Azimut toiture",                  f"{cal.get('azimuth_deg', 180):.0f}°  (180° = Plein sud)"],
            ["Espacement inter-rangées (min.)", f"{cal.get('row_spacing_m', 0):.2f} m  (anti-ombrage solstice hiver)"],
        ]))

        story.append(_subsection_header(f"{sec}.4  Localisation GPS"))
        story.append(_data_table([
            ["Coordonnée", "Valeur"],
            ["Latitude",   f"{cal.get('latitude', 0):.6f}°"],
            ["Longitude",  f"{cal.get('longitude', 0):.6f}°"],
        ]))

        body_sm = ParagraphStyle("bsm_cal", fontName="Helvetica", fontSize=8,
                                 textColor=C_TEXT_SEC, spaceAfter=2 * mm)
        story.append(Paragraph(
            "ℹ L'espacement inter-rangées est calculé pour garantir l'absence d'ombrage "
            "mutuel au solstice d'hiver (élévation solaire minimale 25°). "
            "La capture satellite du site est disponible via la vue carte de l'application.",
            body_sm,
        ))

    # ── Section Équipements ───────────────────────────────────────────────────

    def _add_equipment(self, story: list, sec: int = 6) -> None:
        r = self.report
        equip = getattr(r, "equipment", None)
        if not equip:
            return

        story.append(_section_header(f"{sec}. Équipements du système"))

        inv  = equip.get("inverter", {})
        bat  = equip.get("battery",  {})
        capex = equip.get("capex",   {})

        if inv:
            story.append(_subsection_header(f"{sec}.1  Onduleur"))
            inv_rows = [["Paramètre", "Valeur"]]
            for k, v in inv.items():
                inv_rows.append([k, str(v)])
            story.append(_data_table(inv_rows))

        if bat:
            story.append(_subsection_header(f"{sec}.2  Stockage batterie"))
            bat_rows = [["Paramètre", "Valeur"]]
            for k, v in bat.items():
                bat_rows.append([k, str(v)])
            story.append(_data_table(bat_rows))

        if capex:
            story.append(_subsection_header(f"{sec}.3  Détail CAPEX"))
            capex_rows = [["Poste", "Montant (XOF)"]]
            for k, v in capex.items():
                capex_rows.append([k, _fmt(float(v))])
            story.append(_data_table(capex_rows))

    # ── Section QA ────────────────────────────────────────────────────────────

    def _add_qa(self, story: list, sec: int = 7) -> None:
        qa = self.report.qa
        story.append(_section_header(f"{sec}. Rapport Qualité & Validation"))

        if qa.validations:
            story.append(_subsection_header(f"{sec}.1  Matrice de validation"))
            story.append(self._build_qa_table(
                [["Code", "Critère", "Statut", "Détail"]] +
                [[v.code, v.label, v.status, v.detail] for v in qa.validations]
            ))

        if qa.edge_cases:
            story.append(_subsection_header(f"{sec}.2  Cas limites"))
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

    def _add_appendix(self, story: list, sec: int = 8) -> None:
        story.append(PageBreak())
        story.append(_section_header(f"{sec}. Annexes"))

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

        story.append(_subsection_header("Note technique — Facteur de puissance (cos φ)"))
        story.append(Paragraph(
            "Le <b>facteur de puissance</b> (cos φ) mesure le rapport entre la puissance "
            "active P (kW) et la puissance apparente S (kVA) : <b>S = P / cos φ</b>. "
            "Les charges inductives (climatiseurs, compresseurs, moteurs) présentent "
            "typiquement cos φ = 0,70–0,85, tandis que les charges résistives (chauffage) "
            "ou les alimentations à découpage modernes (LED, onduleurs) atteignent 0,90–1,0.",
            body_sm,
        ))
        story.append(Paragraph(
            "<b>Impact sur le dimensionnement :</b> Un site avec cos φ = 0,80 nécessite "
            "un onduleur capable de délivrer S = P / 0,80 en kVA, soit 25 % de capacité "
            "supplémentaire par rapport aux kW nominaux. Un sous-dimensionnement en kVA "
            "provoque une surcharge thermique, réduit la durée de vie et peut déclencher "
            "les protections de l'onduleur. Recommandation : sélectionner l'onduleur sur "
            "la base de la puissance apparente totale du site avec une marge de 10–20 %.",
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
