"""
Générateur du prompt PDF SolarIntel v2 — avec agents wshobson/agents.
Exécuter : python3 generate_prompt_pdf.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, PageBreak,
    Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from datetime import date

OUTPUT = "SOLARINTEL_V2_PROMPT.pdf"

# ── Palette ──────────────────────────────────────────────────────────────────
C_NAVY    = HexColor("#0F172A")
C_BLUE    = HexColor("#0EA5E9")
C_DARK    = HexColor("#0369A1")
C_AMBER   = HexColor("#F59E0B")
C_GREEN   = HexColor("#22C55E")
C_RED     = HexColor("#EF4444")
C_PURPLE  = HexColor("#7C3AED")
C_ORANGE  = HexColor("#F97316")
C_WHITE   = HexColor("#FFFFFF")
C_SURFACE = HexColor("#F8FAFC")
C_BORDER  = HexColor("#E2E8F0")
C_TEXT    = HexColor("#1E293B")
C_MUTED   = HexColor("#64748B")
C_ROW     = HexColor("#F1F5F9")

PAGE_W, PAGE_H = A4
MARGIN   = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Styles ───────────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

TITLE    = S("title",  fontName="Helvetica-Bold",  fontSize=22, textColor=C_WHITE,  leading=28, alignment=TA_CENTER)
SUBTITLE = S("sub",    fontName="Helvetica",        fontSize=11, textColor=C_BLUE,   leading=15, alignment=TA_CENTER, spaceAfter=4*mm)
H1       = S("h1",     fontName="Helvetica-Bold",  fontSize=13, textColor=C_WHITE,  leading=17)
H2       = S("h2",     fontName="Helvetica-Bold",  fontSize=10, textColor=C_DARK,   leading=14, spaceAfter=2*mm)
H3       = S("h3",     fontName="Helvetica-Bold",  fontSize=9,  textColor=C_NAVY,   leading=13, spaceBefore=2*mm)
BODY     = S("body",   fontName="Helvetica",        fontSize=9,  textColor=C_TEXT,   leading=13, spaceAfter=1*mm, alignment=TA_JUSTIFY)
MONO     = S("mono",   fontName="Courier",          fontSize=8,  textColor=C_NAVY,   leading=12, spaceAfter=1*mm,
             backColor=HexColor("#F1F5F9"), leftIndent=4*mm, rightIndent=4*mm, spaceBefore=1*mm)
BULLET   = S("bullet", fontName="Helvetica",        fontSize=9,  textColor=C_TEXT,   leading=13, leftIndent=6*mm, spaceAfter=0.5*mm)
LABEL    = S("label",  fontName="Helvetica-Bold",  fontSize=8,  textColor=C_MUTED,  leading=11)
NOTE     = S("note",   fontName="Helvetica",        fontSize=8,  textColor=C_MUTED,  leading=11, spaceAfter=2*mm)
CODE_TITLE = S("ct",   fontName="Helvetica-Bold",  fontSize=8,  textColor=C_DARK,   leading=11, spaceBefore=3*mm)

# ── Helpers ──────────────────────────────────────────────────────────────────
def section_banner(text, color=None):
    bg = color or C_DARK
    p  = Paragraph(text, H1)
    t  = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    t.spaceBefore = 6*mm
    t.spaceAfter  = 3*mm
    return t

def sub_banner(text, color=None):
    bg = color or HexColor("#EFF6FF")
    p  = Paragraph(text, H2)
    t  = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("LINEBEFORE",    (0,0),(-1,-1), 3, C_BLUE),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    t.spaceBefore = 4*mm
    t.spaceAfter  = 2*mm
    return t

def two_col_table(rows, w1=0.55):
    cw = [CONTENT_W * w1, CONTENT_W * (1-w1)]
    t  = Table(rows, colWidths=cw)
    cmds = [
        ("FONTNAME",      (0,0),(-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0),(-1,-1), 8.5),
        ("TEXTCOLOR",     (0,0),(-1, 0), C_WHITE),
        ("BACKGROUND",    (0,0),(-1, 0), C_DARK),
        ("ALIGN",         (1,0),(1, -1), "LEFT"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0,i),(-1,i), C_ROW))
    t.setStyle(TableStyle(cmds))
    t.spaceAfter = 3*mm
    return t

def plugin_table(rows):
    cw = [CONTENT_W*0.28, CONTENT_W*0.18, CONTENT_W*0.54]
    t  = Table(rows, colWidths=cw)
    cmds = [
        ("FONTNAME",      (0,0),(-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("TEXTCOLOR",     (0,0),(-1, 0), C_WHITE),
        ("BACKGROUND",    (0,0),(-1, 0), C_PURPLE),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("GRID",          (0,0),(-1,-1), 0.4, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0,i),(-1,i), C_ROW))
    t.setStyle(TableStyle(cmds))
    t.spaceAfter = 3*mm
    return t

def feature_card(icon, title, items, color=None):
    c = color or C_BLUE
    header = Paragraph(f"{icon}  {title}", S("fc", fontName="Helvetica-Bold", fontSize=9,
                        textColor=C_WHITE, leading=13))
    body_lines = [Paragraph(f"• {it}", BULLET) for it in items]
    inner = Table([[header]] + [[b] for b in body_lines], colWidths=[CONTENT_W])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), c),
        ("BACKGROUND",    (0,1),(-1,-1), HexColor("#F8FAFC")),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("BOX",           (0,0),(-1,-1), 0.5, c),
    ]))
    inner.spaceBefore = 2*mm
    inner.spaceAfter  = 3*mm
    return inner

def code_block(lines):
    content = [Paragraph(line or " ", MONO) for line in lines]
    t = Table([[c] for c in content], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#0F172A")),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BLUE),
    ]))
    # override mono color for dark bg
    inner = []
    for line in lines:
        p = Paragraph(line or "&nbsp;",
                      S("code_dark", fontName="Courier", fontSize=8,
                        textColor=HexColor("#7DD3FC"), leading=12))
        inner.append([p])
    t2 = Table(inner, colWidths=[CONTENT_W])
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#0F172A")),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("BOX",           (0,0),(-1,-1), 0.8, C_BLUE),
    ]))
    t2.spaceBefore = 1*mm
    t2.spaceAfter  = 3*mm
    return t2

def sp(n=1):
    return Spacer(1, n*mm)

# ── Page callbacks ────────────────────────────────────────────────────────────
def cover_page(canvas, doc):
    W, H = PAGE_W, PAGE_H
    # Fond dégradé simulé
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Bande bleue centrale
    canvas.setFillColor(C_DARK)
    canvas.rect(0, H*0.35, W, H*0.3, fill=1, stroke=0)
    # Accent orange bas
    canvas.setFillColor(C_AMBER)
    canvas.rect(0, 0, W, 6*mm, fill=1, stroke=0)
    # Accent bleu haut
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, H-6*mm, W, 6*mm, fill=1, stroke=0)

def content_page(canvas, doc):
    W, H = PAGE_W, PAGE_H
    # Header
    canvas.saveState()
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, H-14*mm, W, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(C_BLUE)
    canvas.rect(0, H-14.5*mm, W, 0.5*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(MARGIN, H-9*mm, "SolarIntel v2 — Prompt de Reconstruction")
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_AMBER)
    canvas.drawRightString(W-MARGIN, H-9*mm, f"Page {doc.page}")
    # Footer
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN, 3.5*mm, f"Généré le {date.today().strftime('%d/%m/%Y')}  ·  wshobson/agents × SolarIntel")
    canvas.drawRightString(W-MARGIN, 3.5*mm, "github.com/wshobson/agents  ·  Confidentiel")
    canvas.restoreState()

# ── Story ─────────────────────────────────────────────────────────────────────
def build_story():
    story = []

    # ── PAGE 1 : Couverture ───────────────────────────────────────────────────
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)

    story.append(sp(52))
    story.append(Paragraph("SolarIntel v2", S("cv1", fontName="Helvetica-Bold",
                 fontSize=36, textColor=C_AMBER, leading=42, alignment=TA_CENTER)))
    story.append(sp(4))
    story.append(Paragraph("Prompt de Reconstruction Complète", S("cv2", fontName="Helvetica",
                 fontSize=16, textColor=C_WHITE, leading=20, alignment=TA_CENTER)))
    story.append(sp(2))
    story.append(Paragraph("avec Multi-Agent Orchestration · wshobson/agents", S("cv3",
                 fontName="Helvetica", fontSize=11, textColor=C_BLUE, leading=15, alignment=TA_CENTER)))
    story.append(sp(8))

    # Badges méta
    badges = [
        ["72 Plugins", "112 Agents", "146 Skills", "16 Orchestrateurs"],
        [S("badge_v", fontName="Helvetica-Bold", fontSize=11, textColor=C_AMBER, leading=14, alignment=TA_CENTER)] * 4,
    ]
    badge_data = [
        [
            Paragraph("72\nPlugins",       S("bv", fontName="Helvetica-Bold", fontSize=14, textColor=C_AMBER, leading=17, alignment=TA_CENTER)),
            Paragraph("112\nAgents",       S("bv", fontName="Helvetica-Bold", fontSize=14, textColor=C_GREEN,  leading=17, alignment=TA_CENTER)),
            Paragraph("146\nSkills",       S("bv", fontName="Helvetica-Bold", fontSize=14, textColor=C_BLUE,   leading=17, alignment=TA_CENTER)),
            Paragraph("16\nOrchestrators", S("bv", fontName="Helvetica-Bold", fontSize=14, textColor=C_PURPLE, leading=17, alignment=TA_CENTER)),
        ],
        [
            Paragraph("wshobson/agents", NOTE),
            Paragraph("Opus 4.6 / Sonnet 4.6", NOTE),
            Paragraph("Progressive Disclosure", NOTE),
            Paragraph("Multi-Agent Workflows", NOTE),
        ]
    ]
    badge_t = Table(badge_data, colWidths=[CONTENT_W/4]*4)
    badge_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), HexColor("#1E293B")),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BLUE),
        ("LINEAFTER",     (0,0),(2,-1),  0.3, C_DARK),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    story.append(badge_t)
    story.append(sp(6))
    story.append(Paragraph(
        f"Dakar, Sénégal · {date.today().strftime('%d %B %Y')} · Version 2.0",
        S("date", fontName="Helvetica", fontSize=9, textColor=C_MUTED, alignment=TA_CENTER)
    ))
    story.append(PageBreak())

    # ── SECTION 1 : CONTEXTE ─────────────────────────────────────────────────
    story.append(section_banner("1. Contexte — SolarIntel v1 (État actuel)", C_NAVY))
    story.append(Paragraph(
        "SolarIntel est une application web de dimensionnement photovoltaïque développée pour le marché "
        "sénégalais et ouest-africain. Elle permet de simuler, dimensionner et générer des rapports "
        "professionnels pour des installations solaires résidentielles et commerciales.",
        BODY))
    story.append(sp(2))

    story.append(sub_banner("1.1  Stack technique actuelle"))
    story.append(two_col_table([
        ["Composant",          "Technologie"],
        ["Frontend",           "Vanilla JS · ArcGIS JS SDK 4.30 · TailwindCSS CDN"],
        ["Backend",            "Python 3.11 · FastAPI · Uvicorn"],
        ["Simulation",         "pvlib 0.11+ · PVGIS TMY (API PVGIS Europe)"],
        ["Rapport PDF",        "ReportLab 4.x · Graphiques vectoriels purs"],
        ["Carte",              "ArcGIS WebMercator EPSG:3857 · Sketch Widget"],
        ["IA / LLM",           "CrewAI + Ollama (optionnel) · Recommandations statiques fallback"],
        ["Déploiement",        "Docker (python:3.11-slim) · Render.com Free tier"],
        ["Base de données",    "Aucune — stateless (tout en mémoire/session)"],
    ]))

    story.append(sub_banner("1.2  Fonctionnalités implémentées"))
    feats = [
        ("Calepinage carte",   "Zone polygonale tracée sur ArcGIS · placement auto et manuel de panneaux"),
        ("Simulation pvlib",   "Production annuelle/mensuelle · PR · rendement spécifique · pertes"),
        ("Tarifs SENELEC",     "DPP/DMP/PPP/PMP/Woyofal · tranches T1/T2/T3 · économies avant/après"),
        ("Facteur puissance",  "P/Q/S/cosφ par appareil · alerte si FP<0,80 · dimensionnement kVA onduleur"),
        ("Rapport PDF",        "10+ pages PVSyst-inspired · charts vectoriels · QA matrix · annexes"),
        ("Capture satellite",  "ArcGIS takeScreenshot() → base64 → inséré dans PDF (calepinage)"),
    ]
    for feat, desc in feats:
        story.append(Paragraph(f"<b>{feat}</b> — {desc}", BULLET))
    story.append(sp(2))

    story.append(sub_banner("1.3  Limitations à corriger en v2"))
    limits = [
        "Pas de base de données — perte de toutes les simulations à chaque session",
        "Single-file index.html (2100+ lignes) — maintenabilité critique",
        "Pas d'authentification — impossible de gérer plusieurs clients/projets",
        "Ollama requis localement pour l'IA — pas scalable en production",
        "Pas de tests automatisés (0% coverage) — risque régressions",
        "API PVGIS appelée à chaque simulation — pas de cache — lent",
        "Render.com Free tier : cold start 30-60s — UX dégradée",
        "Pas de monitoring ni d'alertes production",
    ]
    for l in limits:
        story.append(Paragraph(f"• {l}", BULLET))

    story.append(PageBreak())

    # ── SECTION 2 : NOUVELLES FONCTIONNALITÉS ────────────────────────────────
    story.append(section_banner("2. Nouvelles Fonctionnalités — SolarIntel v2", C_PURPLE))

    # Module A
    story.append(KeepTogether([
        feature_card("🏗️", "MODULE A — Architecture SaaS Multi-tenant", [
            "Authentification JWT (email/mot de passe) + OAuth2 Google",
            "Rôles : Admin / Commercial / Technicien / Client (lecture seule)",
            "Multi-projets : chaque utilisateur gère N installations",
            "Dashboard portfolio : carte des sites, KPIs agrégés, alertes",
            "Historique complet : toutes les simulations conservées en DB",
            "API REST versionnée (/api/v2/) avec documentation OpenAPI auto",
        ], C_PURPLE),
    ]))

    story.append(KeepTogether([
        feature_card("📱", "MODULE B — Progressive Web App (PWA) Mobile", [
            "Service Worker + manifest.json → installable sur Android/iOS",
            "Mode hors-ligne : consultation des rapports sans réseau",
            "Capture photo du toit → analyse IA de la surface disponible",
            "Géolocalisation automatique du site (GPS natif)",
            "Formulaire de saisie rapide (devis express en < 5 min)",
            "Partage de rapport PDF directement depuis l'app mobile",
        ], C_GREEN),
    ]))

    story.append(KeepTogether([
        feature_card("🤖", "MODULE C — IA Multi-agent Avancée (wshobson/agents)", [
            "Agent Dimensionnement : recommande automatiquement marque/modèle onduleur/batterie",
            "Agent Optimisation Calepinage : algorithme génétique pour placement optimal",
            "Agent Analyse Prédictive : compare production réelle vs simulée (si données dispo)",
            "Agent Rédaction Rapport : génère l'analyse narrative PVSyst-style via LLM",
            "Agent Vérification QA : valide cohérence technique du projet (8 critères V1-V8)",
            "Orchestrateur full-stack : coordonne tous les agents en parallèle (< 30s)",
        ], C_AMBER),
    ]))

    story.append(KeepTogether([
        feature_card("🌐", "MODULE D — Intégrations Temps Réel", [
            "Open-Meteo API : données météo horaires temps réel (température, irradiance)",
            "SunSpec/Modbus : lecture données onduleurs (production instantanée kW)",
            "WhatsApp Business API : envoi automatique devis PDF au client",
            "SMS (Twilio/Orange) : rappels maintenance et alertes performance",
            "Prix matériaux : scraping hebdomadaire fournisseurs sénégalais (cache Redis)",
            "SENELEC Open Data : mise à jour automatique des grilles tarifaires",
        ], C_ORANGE),
    ]))

    story.append(KeepTogether([
        feature_card("📊", "MODULE E — Rapport Interactif & Simulation Avancée", [
            "Export HTML interactif (graphiques Chart.js) en plus du PDF",
            "Simulation Monte Carlo : intervalles de confiance sur la production (±15%)",
            "Analyse de sensibilité : impact prix électricité ±20% sur ROI/payback",
            "Comparaison multi-scénarios : On-grid vs Hybride vs Off-grid côte à côte",
            "Rapport bilingue : Français / Wolof (localization i18n)",
            "QR code dans le rapport → lien vers dashboard en ligne du projet",
        ], C_RED),
    ]))

    story.append(KeepTogether([
        feature_card("📡", "MODULE F — Monitoring Post-Installation", [
            "Dashboard temps réel : kWh produit aujourd'hui / ce mois / cette année",
            "Graphique production réelle vs simulée (écart en %)",
            "Alertes automatiques : performance < 80% → SMS + email technicien",
            "Rapport mensuel automatique envoyé au client (PDF + WhatsApp)",
            "ROI tracking réel : calcul économies réelles vs factures SENELEC passées",
            "Durée de vie projetée : dégradation réelle mesurée vs modèle 0,5%/an",
        ], C_BLUE),
    ]))

    story.append(KeepTogether([
        feature_card("🗄️", "MODULE G — Base de Données & Performance", [
            "PostgreSQL (Supabase ou Railway) : projets, utilisateurs, simulations, équipements",
            "Cache Redis : résultats PVGIS (TTL 30 jours), sessions, rate limiting",
            "Catalogue équipements enrichi : 200+ panneaux, 50+ onduleurs, 20+ batteries",
            "Full-text search : recherche dans projets et équipements",
            "Export CSV/Excel : données de simulation pour analyse externe",
            "Backup automatique quotidien → S3 / Cloudflare R2",
        ], C_DARK),
    ]))

    story.append(KeepTogether([
        feature_card("🔒", "MODULE H — Sécurité & DevOps Production", [
            "HTTPS obligatoire · CORS strict · Rate limiting par IP et par utilisateur",
            "CI/CD GitHub Actions : lint → tests → build Docker → deploy Render/Railway",
            "Tests unitaires pytest : 90%+ coverage (API, simulation, tarifs SENELEC)",
            "Tests E2E Playwright : parcours utilisateur complet (dessin zone → rapport)",
            "SAST automatique (Bandit + pip-audit) sur chaque PR",
            "Monitoring Grafana Cloud : latence API, erreurs 5xx, alertes PagerDuty",
        ], C_NAVY),
    ]))

    story.append(PageBreak())

    # ── SECTION 3 : SETUP AGENTS ─────────────────────────────────────────────
    story.append(section_banner("3. Setup wshobson/agents — Installation des Plugins", C_DARK))

    story.append(Paragraph(
        "Le système wshobson/agents fournit 112 agents spécialisés organisés en 72 plugins. "
        "Chaque plugin est isolé et ne charge que ses propres agents/skills en contexte, "
        "minimisant la consommation de tokens. Voici la liste des plugins à installer pour SolarIntel v2.",
        BODY))
    story.append(sp(2))

    story.append(sub_banner("3.1  Commandes d'installation"))
    story.append(Paragraph("Étape 1 — Ajouter le marketplace :", CODE_TITLE))
    story.append(code_block([
        "/plugin marketplace add wshobson/agents",
    ]))

    story.append(Paragraph("Étape 2 — Installer les plugins essentiels :", CODE_TITLE))
    story.append(code_block([
        "# Développement Backend",
        "/plugin install python-development",
        "/plugin install backend-development",
        "",
        "# Frontend & Full-Stack",
        "/plugin install javascript-typescript",
        "/plugin install full-stack-orchestration",
        "",
        "# Infrastructure & Base de données",
        "/plugin install database-design",
        "/plugin install cloud-infrastructure",
        "",
        "# Qualité & Sécurité",
        "/plugin install security-scanning",
        "/plugin install comprehensive-review",
        "/plugin install testing-and-tdd",
        "",
        "# Observabilité & Ops",
        "/plugin install observability",
        "",
        "# IA & Orchestration Multi-agent",
        "/plugin install agent-teams",
        "/plugin install conductor",
        "/plugin install llm-applications",
        "",
        "# Documentation",
        "/plugin install documentation",
    ]))

    story.append(sub_banner("3.2  Catalogue des plugins recommandés"))
    story.append(plugin_table([
        ["Plugin",                   "Agents clés",          "Usage SolarIntel v2"],
        ["python-development",       "python-pro\nfastapi-pro\ndjango-pro", "Refactoring backend · FastAPI v2 · async patterns"],
        ["backend-development",      "backend-architect\napi-designer",     "Architecture microservices · REST API design · JWT auth"],
        ["javascript-typescript",    "javascript-pro\ntypescript-pro",      "Refactoring frontend · TypeScript migration · PWA"],
        ["full-stack-orchestration", "orchestrateur 7+ agents",             "Feature complète en 1 commande (backend→frontend→tests)"],
        ["database-design",          "database-architect\nmigrations-pro",  "Schéma PostgreSQL · migrations Alembic · indexation"],
        ["security-scanning",        "security-auditor\nsast-agent",        "OWASP Top 10 · JWT security · CORS · rate limiting"],
        ["comprehensive-review",     "architect-review\ncode-reviewer",     "Revue code avant chaque PR · Opus 4.6"],
        ["testing-and-tdd",          "test-automator\ntdd-coach",           "pytest 90%+ coverage · Playwright E2E · fixtures"],
        ["observability",            "observability-eng",                   "Grafana · Prometheus · alertes · dashboards"],
        ["agent-teams",              "7 équipes prédéfinies",               "Revue parallèle · debug · feature · security audit"],
        ["conductor",                "context-driven dev",                  "Setup projet · tracks · TDD workflow · revert sémantique"],
        ["llm-applications",         "llm-architect\nrag-engineer",         "LangGraph pour agents IA · prompt engineering · RAG"],
        ["cloud-infrastructure",     "cloud-architect\nterraform-pro",      "Migration Render → Railway/Fly.io · Terraform IaC"],
        ["documentation",            "doc-writer\napi-doc-gen",             "README · OpenAPI enrichi · guide utilisateur · ADRs"],
    ]))

    story.append(sub_banner("3.3  Stratégie de modèles (Three-Tier)"))
    story.append(two_col_table([
        ["Tier / Modèle",    "Agents assignés pour SolarIntel v2"],
        ["Opus 4.6 (Tier 1)", "architect-review · security-auditor · backend-architect · database-architect · code-reviewer"],
        ["Sonnet 4.6 (Tier 2/inherit)", "python-pro · fastapi-pro · javascript-pro · llm-architect · observability-eng"],
        ["Haiku 4.5 (Tier 3/4)", "doc-writer · test-automator · deployment-eng · seo-agent · api-doc-gen"],
    ], w1=0.35))

    story.append(PageBreak())

    # ── SECTION 4 : PROMPT PRINCIPAL ─────────────────────────────────────────
    story.append(section_banner("4. PROMPT PRINCIPAL — À Copier-Coller dans Claude Code", C_NAVY))
    story.append(Paragraph(
        "Le prompt ci-dessous est conçu pour être soumis directement à Claude Code après l'installation "
        "des plugins. Il décrit l'intégralité du projet v2 et orchestre les agents automatiquement.",
        BODY))
    story.append(sp(3))

    # ─────────────────────────────────────────────────
    # GRAND PROMPT — formaté en sections de code
    # ─────────────────────────────────────────────────
    story.append(sub_banner("4.1  Bloc d'initialisation Conductor"))
    story.append(code_block([
        "/conductor:setup",
    ]))
    story.append(Paragraph(
        "Quand Conductor demande le contexte, fournir les informations suivantes :", BODY))
    story.append(code_block([
        "PRODUCT VISION:",
        "SolarIntel v2 est une plateforme SaaS de dimensionnement photovoltaïque pour",
        "l'Afrique de l'Ouest (Sénégal). Elle permet aux installateurs solaires de",
        "simuler, dimensionner et monitorer des installations PV via une interface",
        "web + mobile, avec rapports PDF automatiques inspirés de PVSyst.",
        "",
        "TECH STACK:",
        "- Backend  : Python 3.11 · FastAPI · PostgreSQL · Redis · Alembic",
        "- Frontend : React 18 + TypeScript · Vite · TailwindCSS · ArcGIS JS SDK 4.30",
        "- IA       : LangGraph · Claude API (Anthropic) · pvlib 0.11+",
        "- Infra    : Docker · GitHub Actions CI/CD · Railway.app (prod)",
        "- PDF      : ReportLab · (HTML interactif via Chart.js)",
        "",
        "WORKFLOW RULES:",
        "- TDD obligatoire : écrire les tests avant le code (pytest + Playwright)",
        "- Chaque PR doit passer : lint (ruff) · type-check (mypy) · tests · SAST",
        "- Les agents Opus 4.6 valident toute décision d'architecture",
        "- Maximum 300 lignes par fichier Python · 200 lignes par composant React",
        "",
        "STYLE GUIDE:",
        "- Python : PEP 8 · type hints complets · docstrings Google format",
        "- TypeScript : strict mode · composants fonctionnels · hooks custom",
        "- API : REST versionnée /api/v2/ · OpenAPI 3.1 · pagination cursor-based",
        "- Noms variables : snake_case (Python) · camelCase (TS) · kebab-case (CSS)",
    ]))

    story.append(sub_banner("4.2  Prompt de reconstruction complète"))
    story.append(code_block([
        "Je veux reconstruire SolarIntel v1 (application de dimensionnement PV) en v2",
        "avec une architecture professionnelle SaaS. Voici le contexte complet :",
        "",
        "=== PROJET EXISTANT ===",
        "- index.html (2100+ lignes) : Vanilla JS + ArcGIS + TailwindCSS CDN",
        "- solarintel/api.py : FastAPI · /api/simulate (pvlib) · /health",
        "- solarintel/api_report.py : /api/report (PDF ReportLab 10+ pages)",
        "- solarintel/api_senelec.py : tarifs DPP/DMP/PPP/PMP/Woyofal",
        "- solarintel/reports/generator.py : moteur PDF (sections A/B/C)",
        "- solarintel/reports/charts.py : graphiques vectoriels ReportLab",
        "- Déployé sur Render.com (Docker, free tier)",
        "",
        "=== FONCTIONNALITÉS V1 À CONSERVER ===",
        "1. Simulation pvlib (TMY PVGIS) avec pertes système",
        "2. Calepinage ArcGIS (zone polygonale + placement panneaux)",
        "3. Analyse SENELEC (tranches T1/T2/T3, Woyofal, économies 12 mois)",
        "4. Facteur puissance (P/Q/S/cosφ, alerte FP<0.80, kVA onduleur)",
        "5. Rapport PDF PVSyst-inspired (capture satellite, graphiques, QA)",
        "6. Catalogue équipements (JA Solar, Trina, GOODWE, GROWATT, DEYE)",
        "",
        "=== NOUVELLES FONCTIONNALITÉS V2 ===",
        "",
        "MODULE A — Architecture SaaS Multi-tenant:",
        "  - Auth JWT (FastAPI-Users) + OAuth2 Google",
        "  - Rôles : Admin / Commercial / Technicien / Client",
        "  - Projets multi-sites par utilisateur",
        "  - PostgreSQL + Alembic migrations",
        "  - Redis cache (sessions + résultats PVGIS TTL 30j)",
        "",
        "MODULE B — Frontend React + TypeScript:",
        "  - Migrer index.html → React 18 + Vite + TypeScript strict",
        "  - Conserver ArcGIS JS SDK 4.30 (via @arcgis/core)",
        "  - PWA (manifest + service worker) pour mobile",
        "  - State management : Zustand",
        "  - Routing : React Router v6",
        "",
        "MODULE C — IA Multi-agent (LangGraph + Claude API):",
        "  - Agent 1 : Dimensionnement automatique équipements",
        "  - Agent 2 : Optimisation calepinage (algorithme génétique)",
        "  - Agent 3 : Analyse prédictive (production réelle vs simulée)",
        "  - Agent 4 : Rédaction narrative du rapport (Claude claude-opus-4-6)",
        "  - Orchestrateur LangGraph : parallélisme agents → < 30s total",
        "",
        "MODULE D — Intégrations :",
        "  - Open-Meteo API : météo temps réel pour correction production",
        "  - WhatsApp Business API : envoi devis automatique",
        "  - Webhook inverters : réception données production (SunSpec)",
        "",
        "MODULE E — Rapport Avancé :",
        "  - Export HTML interactif (Chart.js) en plus du PDF",
        "  - Simulation Monte Carlo (N=1000, intervalles ±15%)",
        "  - Analyse sensibilité prix électricité (±10%, ±20%, ±30%)",
        "  - Comparaison scénarios (on-grid vs hybride vs off-grid)",
        "",
        "MODULE F — Monitoring Post-installation :",
        "  - Dashboard temps réel (WebSocket → données inverter)",
        "  - Alertes performance (< 80% production attendue)",
        "  - Rapport mensuel automatique (PDF + WhatsApp)",
        "",
        "MODULE H — DevOps :",
        "  - GitHub Actions : ruff + mypy + pytest + playwright + docker build",
        "  - Coverage minimum 90% (backend) et 80% (frontend)",
        "  - Deploy automatique Railway.app sur merge main",
        "  - Monitoring Grafana Cloud (métriques FastAPI + PostgreSQL)",
        "",
        "=== CONTRAINTES NON NÉGOCIABLES ===",
        "- Aucune perte de fonctionnalité v1 pendant la migration",
        "- API v1 maintenue en parallèle (/api/v1/) pendant 3 mois",
        "- PDF ReportLab conservé (pas de dépendance Puppeteer/Chrome)",
        "- ArcGIS JS SDK 4.30 conservé (licence existante)",
        "- Sénégal-first : tarifs SENELEC, FCFA, Wolof i18n optionnel",
        "- Coût infrastructure < 50 USD/mois (Railway Hobby plan)",
        "- Temps de réponse /api/simulate < 5s (avec cache Redis)",
        "",
        "=== PLAN D'EXÉCUTION DEMANDÉ ===",
        "Utilise /full-stack-orchestration:full-stack-feature pour chaque module.",
        "Commence par MODULE G (base de données) car tous les autres en dépendent.",
        "Utilise /agent-teams:team-review sur chaque module terminé avant de passer",
        "au suivant. Génère les tests en parallèle avec /agent-teams:team-feature.",
        "",
        "Commence par MODULE G maintenant.",
    ]))

    story.append(sub_banner("4.3  Commandes d'orchestration par module"))
    story.append(plugin_table([
        ["Module",    "Commande principale",    "Description"],
        ["G — DB",    "/full-stack-orchestration:full-stack-feature 'PostgreSQL schema + Alembic migrations pour SolarIntel v2'", "Crée le schéma complet : users, projects, simulations, equipment, reports"],
        ["A — Auth",  "/full-stack-orchestration:full-stack-feature 'JWT auth + roles pour FastAPI SolarIntel'",                  "FastAPI-Users · JWT · OAuth2 Google · middleware rôles"],
        ["B — React", "/javascript-typescript:typescript-pro 'Migrer index.html SolarIntel vers React 18 + TypeScript + Vite'",  "Composants React · hooks · state Zustand · ArcGIS @arcgis/core"],
        ["C — IA",    "/llm-applications:langchain-pro 'LangGraph multi-agent pour SolarIntel : dimensionnement + calepinage'",  "4 agents spécialisés · orchestrateur parallèle · Claude API"],
        ["D — Intég", "/backend-development:api-designer 'Intégrations WebSocket + WhatsApp + Open-Meteo pour SolarIntel'",     "Webhooks · Open-Meteo · Twilio WhatsApp · SunSpec Modbus"],
        ["H — DevOps","/cloud-infrastructure:terraform-pro 'GitHub Actions + Railway.app CI/CD pour SolarIntel v2'",            "Pipeline CI/CD · tests · SAST · deploy auto · monitoring"],
        ["Review",    "/agent-teams:team-review src/ --reviewers security,performance,architecture",                             "Revue parallèle par 3 agents (Opus 4.6) avant merge"],
    ]))

    story.append(PageBreak())

    # ── SECTION 5 : ARCHITECTURE V2 ──────────────────────────────────────────
    story.append(section_banner("5. Architecture Cible — SolarIntel v2", C_DARK))

    story.append(sub_banner("5.1  Schéma de base de données (PostgreSQL)"))
    story.append(code_block([
        "-- Tables principales",
        "users          (id, email, role, company, created_at)",
        "projects       (id, user_id, name, latitude, longitude, polygon_geojson)",
        "simulations    (id, project_id, panel_count, peak_kwc, annual_kwh, ...)",
        "equipment      (id, project_id, inverter_model, battery_model, ...)",
        "reports        (id, simulation_id, pdf_path, html_path, generated_at)",
        "monitoring     (id, project_id, timestamp, production_kwh, irradiance)",
        "tariff_history (id, tariff_code, effective_date, t1, t2, t3)",
        "",
        "-- Cache (Redis TTL)",
        "pvgis:{lat}:{lon}    → résultats TMY (TTL 30 jours)",
        "session:{token}      → données utilisateur (TTL 24h)",
        "tariff:senelec       → grille tarifaire (TTL 7 jours)",
    ]))

    story.append(sub_banner("5.2  Structure des dossiers v2"))
    story.append(code_block([
        "solarintel-v2/",
        "├── backend/",
        "│   ├── app/",
        "│   │   ├── api/v2/          # Endpoints FastAPI",
        "│   │   │   ├── auth.py      # JWT + OAuth2",
        "│   │   │   ├── projects.py  # CRUD projets",
        "│   │   │   ├── simulate.py  # pvlib simulation",
        "│   │   │   ├── report.py    # PDF + HTML",
        "│   │   │   └── monitoring.py# WebSocket données réelles",
        "│   │   ├── agents/          # LangGraph agents IA",
        "│   │   │   ├── dimensioning.py",
        "│   │   │   ├── calepinage.py",
        "│   │   │   ├── prediction.py",
        "│   │   │   └── orchestrator.py",
        "│   │   ├── models/          # SQLAlchemy ORM",
        "│   │   ├── schemas/         # Pydantic v2",
        "│   │   ├── services/        # Logique métier",
        "│   │   └── config/          # SENELEC, constantes",
        "│   ├── tests/               # pytest (90%+ coverage)",
        "│   └── alembic/             # Migrations DB",
        "├── frontend/",
        "│   ├── src/",
        "│   │   ├── components/      # Composants React",
        "│   │   │   ├── Map/         # ArcGIS wrapper",
        "│   │   │   ├── Report/      # Prévisualisation rapport",
        "│   │   │   └── Dashboard/   # Monitoring",
        "│   │   ├── pages/           # React Router",
        "│   │   ├── stores/          # Zustand stores",
        "│   │   ├── hooks/           # Custom hooks",
        "│   │   └── api/             # Client API typesafe",
        "│   └── tests/               # Playwright E2E",
        "├── .github/workflows/       # CI/CD GitHub Actions",
        "├── docker-compose.yml       # Dev local (app+db+redis)",
        "└── railway.toml             # Config Railway.app",
    ]))

    story.append(sub_banner("5.3  Flux multi-agent LangGraph"))
    story.append(code_block([
        "User Input: panneau_count=20, location=(14.69, -17.44), appliances=[...]",
        "       ↓",
        "Orchestrator (LangGraph StateGraph)",
        "       ├──► Agent Dimensionnement  (Sonnet 4.6) → recommande onduleur kVA",
        "       ├──► Agent Simulation       (pvlib sync)  → production mensuelle 12m",
        "       ├──► Agent SENELEC          (Python calc) → économies avant/après",
        "       └──► Agent Rédaction        (Opus 4.6)    → narrative rapport",
        "       ↓ (parallèle, timeout 25s)",
        "Merge Results → SolarReport v2 complet",
        "       ↓",
        "Agent QA (Sonnet 4.6) → valide 8 critères V1-V8 (FP, kVA, coverage...)",
        "       ↓",
        "Generator → PDF (ReportLab) + HTML interactif (Chart.js) + WhatsApp",
    ]))

    story.append(PageBreak())

    # ── SECTION 6 : ROADMAP ──────────────────────────────────────────────────
    story.append(section_banner("6. Roadmap d'Implémentation", C_GREEN))

    story.append(two_col_table([
        ["Phase / Sprint",  "Contenu & Livrables"],
        ["Sprint 1 (S1-S2)\nFondations DB",
         "PostgreSQL + Alembic · FastAPI-Users JWT · Redis cache · Docker compose dev · Tests auth"],
        ["Sprint 2 (S3-S4)\nMigration Frontend",
         "React 18 + Vite + TS · Composants ArcGIS · Zustand stores · Routing · PWA manifest"],
        ["Sprint 3 (S5-S6)\nAPI v2 + Cache",
         "/api/v2/simulate (pvlib + cache Redis) · /api/v2/projects CRUD · OpenAPI complet"],
        ["Sprint 4 (S7-S8)\nAgents IA LangGraph",
         "4 agents spécialisés · Orchestrateur parallèle · Intégration Claude API · Tests LLM"],
        ["Sprint 5 (S9-S10)\nRapport Avancé",
         "Monte Carlo · Analyse sensibilité · Export HTML Chart.js · Comparaison scénarios"],
        ["Sprint 6 (S11-S12)\nIntégrations",
         "Open-Meteo · WhatsApp Business · Webhook inverters · i18n Wolof optionnel"],
        ["Sprint 7 (S13-S14)\nMonitoring + DevOps",
         "Dashboard temps réel WebSocket · GitHub Actions CI/CD · Grafana · Railway deploy"],
        ["Sprint 8 (S15-S16)\nQualité & Launch",
         "Coverage 90%+ · Playwright E2E · SAST audit · Load testing · Documentation complète"],
    ], w1=0.28))

    story.append(sp(3))
    story.append(sub_banner("6.1  Commande de lancement immédiat"))
    story.append(Paragraph(
        "Une fois les plugins installés, lancer la reconstruction avec cette séquence :", BODY))
    story.append(code_block([
        "# 1. Initialiser le projet Conductor",
        "/conductor:setup",
        "",
        "# 2. Créer le premier track (Module G — Base de données)",
        "/conductor:new-track 'Base de données PostgreSQL + authentification JWT'",
        "",
        "# 3. Implémenter avec TDD",
        "/conductor:implement",
        "",
        "# 4. Revue multi-agent avant merge",
        "/agent-teams:team-review backend/ --reviewers security,performance,architecture",
        "",
        "# 5. Feature React (après DB validée)",
        "/full-stack-orchestration:full-stack-feature 'Migration React 18 + TypeScript SolarIntel'",
        "",
        "# 6. Agents IA LangGraph",
        "/llm-applications:langchain-pro 'Orchestrateur multi-agent PV SolarIntel v2'",
    ]))

    story.append(PageBreak())

    # ── SECTION 7 : RESSOURCES ────────────────────────────────────────────────
    story.append(section_banner("7. Ressources & Références", C_NAVY))

    story.append(sub_banner("7.1  Dépôts et documentation"))
    story.append(two_col_table([
        ["Ressource",                  "URL"],
        ["wshobson/agents",            "github.com/wshobson/agents"],
        ["Claude Code Documentation",  "docs.anthropic.com/claude-code"],
        ["Plugin Reference",           "github.com/wshobson/agents/docs/plugins.md"],
        ["Agent Reference",            "github.com/wshobson/agents/docs/agents.md"],
        ["Skills Reference",           "github.com/wshobson/agents/docs/skills.md"],
        ["FastAPI",                    "fastapi.tiangolo.com"],
        ["pvlib",                      "pvlib.readthedocs.io"],
        ["LangGraph",                  "langchain-ai.github.io/langgraph"],
        ["ArcGIS JS SDK 4.x",          "developers.arcgis.com/javascript/latest"],
        ["Railway.app",                "railway.app/docs"],
        ["PVGIS API",                  "re.jrc.ec.europa.eu/pvg_tools/en"],
        ["ReportLab",                  "docs.reportlab.com"],
        ["Playwright",                 "playwright.dev"],
    ]))

    story.append(sub_banner("7.2  Variables d'environnement requises"))
    story.append(code_block([
        "# Backend (.env)",
        "DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/solarintel",
        "REDIS_URL=redis://localhost:6379/0",
        "SECRET_KEY=<32 chars random>",
        "ANTHROPIC_API_KEY=sk-ant-...",
        "GOOGLE_CLIENT_ID=...",
        "GOOGLE_CLIENT_SECRET=...",
        "WHATSAPP_TOKEN=...",
        "WHATSAPP_PHONE_ID=...",
        "",
        "# Optionnel",
        "OLLAMA_HOST=http://localhost:11434   # fallback LLM local",
        "OLLAMA_MODEL=llama3",
        "GRAFANA_API_KEY=...",
        "SENTRY_DSN=...",
    ]))

    story.append(sp(4))
    story.append(Paragraph(
        "Ce document constitue le cahier des charges technique complet pour SolarIntel v2. "
        "Le prompt de la section 4 peut être soumis directement à Claude Code après installation "
        "des plugins wshobson/agents. L'orchestration multi-agent gérera automatiquement "
        "la coordination entre les agents spécialisés pour chaque module.",
        S("final", fontName="Helvetica", fontSize=9, textColor=C_MUTED,
          leading=14, alignment=TA_JUSTIFY)
    ))

    return story


# ── Build PDF ──────────────────────────────────────────────────────────────────
def main():
    story = build_story()

    # Cover frame (no margins)
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H,
                        leftPadding=MARGIN+4*mm, rightPadding=MARGIN+4*mm,
                        topPadding=0, bottomPadding=0, id="cover")

    # Content frame
    content_frame = Frame(
        MARGIN + 2*mm,
        10*mm + MARGIN,
        CONTENT_W - 2*mm,
        PAGE_H - 16*mm - 10*mm - 2*MARGIN,
        id="content",
    )

    doc = BaseDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=14*mm + MARGIN, bottomMargin=12*mm + MARGIN,
    )
    doc.addPageTemplates([
        PageTemplate(id="cover",   frames=[cover_frame],   onPage=cover_page),
        PageTemplate(id="content", frames=[content_frame], onPage=content_page),
    ])

    # Injecter le template "content" après la cover
    from reportlab.platypus import NextPageTemplate
    story.insert(0, NextPageTemplate("content"))
    story.insert(1, PageBreak())

    doc.build(story)
    print(f"PDF généré : {OUTPUT}")


if __name__ == "__main__":
    main()
