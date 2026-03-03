"""
Thème impression pour les rapports PDF SolarIntel.

Traduit le UI_THEME (fond sombre écran) vers un thème fond blanc impression
tout en conservant les accents Solar Blue et Amber.
"""

from __future__ import annotations

from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm

from solarintel.config.constants import UI_THEME


class ReportTheme:
    """Palette et styles ReportLab adaptés à l'impression."""

    # -- Couleurs (conservation des accents, fond inversé) ------------------
    PRIMARY: Color = HexColor(UI_THEME["primary"])          # #0EA5E9
    PRIMARY_DARK: Color = HexColor(UI_THEME["primary_dark"])  # #0369A1
    ACCENT: Color = HexColor(UI_THEME["accent"])            # #F59E0B
    SUCCESS: Color = HexColor(UI_THEME["success"])          # #22C55E
    ERROR: Color = HexColor(UI_THEME["error"])              # #EF4444
    WARNING: Color = HexColor("#F97316")                     # Orange-500

    # Impression : fond clair
    BACKGROUND: Color = HexColor("#FFFFFF")
    SURFACE: Color = HexColor("#F8FAFC")         # Slate-50
    SURFACE_ALT: Color = HexColor("#F1F5F9")     # Slate-100
    TEXT: Color = HexColor("#0F172A")             # Slate-900
    TEXT_SECONDARY: Color = HexColor("#475569")   # Slate-600
    TEXT_LIGHT: Color = HexColor("#94A3B8")       # Slate-400
    BORDER: Color = HexColor("#CBD5E1")           # Slate-300

    # Cover page
    COVER_BG: Color = HexColor(UI_THEME["primary_dark"])
    COVER_TEXT: Color = HexColor("#FFFFFF")

    # -- Polices (built-in ReportLab) ---------------------------------------
    FONT_SANS: str = "Helvetica"
    FONT_SANS_BOLD: str = "Helvetica-Bold"
    FONT_MONO: str = "Courier"

    # -- Dimensions ---------------------------------------------------------
    PAGE_MARGIN: float = 20 * mm
    HEADER_HEIGHT: float = 18 * mm
    FOOTER_HEIGHT: float = 12 * mm

    # -- Tailles tableau ----------------------------------------------------
    TABLE_HEADER_BG: Color = PRIMARY_DARK
    TABLE_HEADER_TEXT: Color = HexColor("#FFFFFF")
    TABLE_ROW_ALT: Color = SURFACE_ALT

    @classmethod
    def get_styles(cls) -> dict[str, ParagraphStyle]:
        """Retourne un dictionnaire de styles de paragraphe."""
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "ReportTitle",
                parent=base["Title"],
                fontName=cls.FONT_SANS_BOLD,
                fontSize=24,
                textColor=cls.PRIMARY_DARK,
                spaceAfter=6 * mm,
                alignment=TA_LEFT,
            ),
            "heading1": ParagraphStyle(
                "ReportH1",
                parent=base["Heading1"],
                fontName=cls.FONT_SANS_BOLD,
                fontSize=16,
                textColor=cls.PRIMARY_DARK,
                spaceBefore=8 * mm,
                spaceAfter=4 * mm,
                alignment=TA_LEFT,
            ),
            "heading2": ParagraphStyle(
                "ReportH2",
                parent=base["Heading2"],
                fontName=cls.FONT_SANS_BOLD,
                fontSize=13,
                textColor=cls.TEXT,
                spaceBefore=5 * mm,
                spaceAfter=3 * mm,
                alignment=TA_LEFT,
            ),
            "body": ParagraphStyle(
                "ReportBody",
                parent=base["Normal"],
                fontName=cls.FONT_SANS,
                fontSize=10,
                textColor=cls.TEXT,
                leading=14,
                spaceAfter=2 * mm,
                alignment=TA_JUSTIFY,
            ),
            "body_small": ParagraphStyle(
                "ReportBodySmall",
                parent=base["Normal"],
                fontName=cls.FONT_SANS,
                fontSize=8,
                textColor=cls.TEXT_SECONDARY,
                leading=11,
                spaceAfter=1 * mm,
            ),
            "mono": ParagraphStyle(
                "ReportMono",
                parent=base["Code"],
                fontName=cls.FONT_MONO,
                fontSize=8,
                textColor=cls.TEXT,
                leading=10,
                spaceAfter=2 * mm,
            ),
            "cover_title": ParagraphStyle(
                "CoverTitle",
                fontName=cls.FONT_SANS_BOLD,
                fontSize=32,
                textColor=cls.COVER_TEXT,
                alignment=TA_CENTER,
                spaceAfter=5 * mm,
            ),
            "cover_subtitle": ParagraphStyle(
                "CoverSubtitle",
                fontName=cls.FONT_SANS,
                fontSize=16,
                textColor=cls.COVER_TEXT,
                alignment=TA_CENTER,
                spaceAfter=3 * mm,
            ),
            "kpi_value": ParagraphStyle(
                "KPIValue",
                fontName=cls.FONT_SANS_BOLD,
                fontSize=20,
                textColor=cls.PRIMARY,
                alignment=TA_CENTER,
            ),
            "kpi_label": ParagraphStyle(
                "KPILabel",
                fontName=cls.FONT_SANS,
                fontSize=9,
                textColor=cls.TEXT_SECONDARY,
                alignment=TA_CENTER,
            ),
            "table_header": ParagraphStyle(
                "TableHeader",
                fontName=cls.FONT_SANS_BOLD,
                fontSize=9,
                textColor=cls.TABLE_HEADER_TEXT,
                alignment=TA_CENTER,
            ),
            "table_cell": ParagraphStyle(
                "TableCell",
                fontName=cls.FONT_SANS,
                fontSize=9,
                textColor=cls.TEXT,
                alignment=TA_LEFT,
            ),
        }
