# Guide complet : Generation de rapports PDF

Manuel d'utilisation du module `solarintel.reports`.

---

## Table des matieres

1. [Apercu](#1-apercu)
2. [Utilisation via CLI](#2-utilisation-via-cli)
3. [Utilisation via API Python](#3-utilisation-via-api-python)
4. [Structure du rapport](#4-structure-du-rapport)
5. [Modeles de donnees](#5-modeles-de-donnees)
6. [Parseur de sortie CrewAI](#6-parseur-de-sortie-crewai)
7. [Personnalisation du theme](#7-personnalisation-du-theme)
8. [Graphiques](#8-graphiques)
9. [Logo personnalise](#9-logo-personnalise)
10. [Exemples complets](#10-exemples-complets)
11. [Depannage](#11-depannage)

---

## 1. Apercu

Le module genere un document PDF A4 professionnel avec :

- **Page de garde** plein ecran (fond bleu `#0369A1`, logo centre)
- **En-tete** sur chaque page : logo miniature + nom entreprise + trait separateur
- **Pied de page** sur chaque page : date de generation + numero de page
- **7 sections** : resume executif, configuration, simulation, economie, QA, annexes
- **Graphiques vectoriels** : barres (production mensuelle) et ligne (cashflow 25 ans)
- **Tableaux** avec alternance de couleurs et en-tetes colores

### Pipeline de donnees

```
crew.kickoff()  ──>  texte brut  ──>  parse_crew_output()  ──>  SolarReport
                                                                      |
                                                                      v
                                                            ReportGenerator.generate()
                                                                      |
                                                                      v
                                                              rapport_solarintel.pdf
```

---

## 2. Utilisation via CLI

### Commande minimale

```bash
python main.py --brief-only backend --generate-report
```

Cela genere `./rapport_solarintel.pdf` dans le repertoire courant.

### Toutes les options

```bash
python main.py --generate-report \
    --logo /chemin/vers/mon_logo.png \
    --company-name "Solair Senegal SARL" \
    --report-title "Etude de faisabilite PV - Site Thies" \
    --output-dir ./rapports \
    --lat 14.79 \
    --lon -16.93 \
    --panel-power 400
```

### Options de rapport

| Option | Description | Defaut |
|--------|-------------|--------|
| `--generate-report` | Active la generation du PDF | Desactive |
| `--logo CHEMIN` | Chemin vers un fichier image PNG/JPG | `assets/logo_solarintel.png` |
| `--company-name NOM` | Nom affiche dans l'en-tete et la couverture | `SolarIntel` |
| `--report-title TITRE` | Titre principal sur la page de garde | `Rapport de Dimensionnement Solaire` |
| `--output-dir DOSSIER` | Repertoire ou le PDF sera ecrit | `.` (repertoire courant) |

### Modes de fonctionnement

```bash
# Mode 1 : Brief seul + rapport
python main.py --brief-only backend --generate-report

# Mode 2 : Pipeline CrewAI complet + rapport (necessite Ollama)
python main.py --generate-report

# Mode 3 : Pipeline complet avec parametres personnalises
python main.py --generate-report \
    --model codellama \
    --lat 14.69 --lon -17.45 \
    --panel-power 545 \
    --company-name "SolarTech"
```

---

## 3. Utilisation via API Python

### Exemple minimal

```python
from solarintel.reports import SolarReport, ReportGenerator

# Creer un rapport avec valeurs par defaut
report = SolarReport()

# Generer le PDF
gen = ReportGenerator(report)
chemin = gen.generate("mon_rapport.pdf")
print(f"PDF cree : {chemin}")
```

### Exemple complet avec donnees

```python
from solarintel.reports import (
    SolarReport,
    SystemConfig,
    SimulationResults,
    EconomicAnalysis,
    QAReport,
    QAValidation,
    ReportGenerator,
)

# 1. Configuration du systeme
system = SystemConfig(
    panel_brand="JA Solar",
    panel_model="JAM72S30-545/MR",
    panel_power_wc=545,
    panel_efficiency=0.211,
    panel_count=20,
    total_power_kwc=10.9,
    location_name="Dakar, Senegal",
    latitude=14.6928,
    longitude=-17.4467,
    altitude=22,
    orientation_azimuth=180,  # plein sud
    tilt=15,                  # 15 degres
)

# 2. Resultats de simulation
simulation = SimulationResults(
    annual_production_kwh=16350,
    monthly_production_kwh=[
        1050, 1150, 1450, 1500, 1600, 1550,
        1400, 1350, 1300, 1250, 1100, 1050,
    ],
    specific_yield_kwh_kwc=1500,
    performance_ratio=0.82,
    soiling_loss_pct=2.0,
    mismatch_loss_pct=1.0,
    wiring_loss_pct=1.5,
    availability_loss_pct=1.0,
    temperature_loss_pct=3.0,
    total_losses_pct=8.5,
)

# 3. Analyse economique
economics = EconomicAnalysis(
    total_cost_xof=7_085_000,
    cost_per_kwc_xof=650_000,
    lcoe_xof_kwh=52.3,
    roi_pct=127.0,
    payback_years=8.2,
    npv_xof=4_500_000,
    annual_savings_xof=1_929_300,
    cashflow_cumulative=[
        -7_085_000 + i * 1_929_300 for i in range(25)
    ],
)

# 4. Rapport QA
qa = QAReport(
    validations=[
        QAValidation(code="V1", label="Coherence puissance crete",
                     status="PASS", detail="10.9 kWc OK"),
        QAValidation(code="V2", label="Production vs irradiation",
                     status="PASS", detail="1500 kWh/kWc coherent"),
        QAValidation(code="V3", label="Performance ratio",
                     status="PASS", detail="PR=82% dans la norme"),
        QAValidation(code="V4", label="Bilan des pertes",
                     status="PASS", detail="8.5% total OK"),
        QAValidation(code="V5", label="LCOE vs tarif SENELEC",
                     status="PASS", detail="52.3 < 118 FCFA/kWh"),
        QAValidation(code="V6", label="Orientation azimut",
                     status="PASS", detail="180 deg (sud) optimal"),
        QAValidation(code="V7", label="Inclinaison",
                     status="PASS", detail="15 deg adapte Dakar"),
        QAValidation(code="V8", label="Degradation annuelle",
                     status="PASS", detail="0.5%/an standard"),
        QAValidation(code="V9", label="Duree de vie",
                     status="PASS", detail="25 ans conforme"),
        QAValidation(code="V10", label="Donnees meteo TMY",
                     status="PASS", detail="PVGIS source fiable"),
    ],
    edge_cases=[
        QAValidation(code="EC1", label="Panneau 0 Wc",
                     status="PASS", detail="Erreur correctement levee"),
        QAValidation(code="EC2", label="Lat/Lon invalides",
                     status="PASS", detail="Validation OK"),
        QAValidation(code="EC3", label="Consommation nulle",
                     status="WARNING", detail="ROI infini gere"),
        QAValidation(code="EC4", label="Surface insuffisante",
                     status="PASS", detail="Alerte utilisateur"),
        QAValidation(code="EC5", label="Ombrage >50%",
                     status="PASS", detail="Avertissement affiche"),
        QAValidation(code="EC6", label="Hors couverture PVGIS",
                     status="PASS", detail="Fallback donnees locales"),
    ],
    verdict="PASS",
    notes="Toutes les validations passent. Systeme correctement dimensionne.",
)

# 5. Assembler le rapport
report = SolarReport(
    project_name="Installation PV Dakar",
    company_name="SolarTech Senegal",
    report_title="Etude de faisabilite photovoltaique",
    system=system,
    simulation=simulation,
    economics=economics,
    qa=qa,
)

# 6. Generer le PDF
gen = ReportGenerator(
    report=report,
    logo_path="assets/logo_solarintel.png",
    company_name="SolarTech Senegal",
)
chemin = gen.generate("rapport_dakar.pdf")
print(f"PDF genere : {chemin}")
```

### Utiliser le parseur sur une sortie CrewAI

```python
from solarintel.reports import parse_crew_output, ReportGenerator

# Sortie brute de crew.kickoff()
raw = str(result)

# Parser automatiquement (JSON ou regex)
report = parse_crew_output(raw, project=None)

# Generer le PDF
gen = ReportGenerator(report, logo_path="assets/logo_solarintel.png")
gen.generate("rapport.pdf")
```

---

## 4. Structure du rapport

Le PDF genere contient les sections suivantes :

### Page 1 : Page de garde

- Fond plein couleur `primary_dark` (#0369A1)
- Logo centre (50x50 mm)
- Titre du rapport (police 32pt, blanc)
- Nom du site / localisation
- Date de generation (format JJ/MM/AAAA)
- Nom de l'entreprise

### Page 2+ : Resume executif

- Texte de synthese auto-genere a partir des donnees (ou texte libre via `executive_summary`)
- **4 boites KPI** en ligne :
  - Production annuelle (kWh/an)
  - Ratio de performance (%)
  - Retour sur investissement (ans)
  - LCOE (XOF/kWh)

### Configuration systeme

- **Tableau panneaux** : marque, modele, puissance, efficacite, nombre, puissance totale
- **Tableau localisation** : site, lat/lon, altitude, azimut, inclinaison

### Simulation photovoltaique

- **Tableau KPIs** : production annuelle, rendement specifique, PR
- **Graphique barres** : production mensuelle (12 barres, Jan-Dec)
- **Tableau pertes** : salissure, mismatch, cablage, disponibilite, temperature, total

### Analyse economique

- **Tableau financier** : cout total, cout/kWc, LCOE, ROI, payback, VAN, economie annuelle
- **Graphique ligne** : cashflow cumule sur 25 ans (point de rentabilite visible)

### Rapport QA

- **Matrice de validation** (V1-V10) : tableau avec coloration par statut
  - **PASS** : texte vert
  - **FAIL** : texte rouge
  - **WARNING** : texte orange
- **Cas limites** (EC1-EC6) : meme format
- **Verdict global** : PASS (vert) ou FAIL (rouge) en grand

### Annexes

- Liste des modules pvlib utilises
- Constantes economiques appliquees
- Methodologie de simulation
- Formules cles (LCOE, ROI, Payback, PR)
- Sortie brute CrewAI (si disponible, tronquee a 5000 caracteres)

---

## 5. Modeles de donnees

Tous les modeles sont dans `solarintel/reports/models.py` et utilisent Pydantic v2.

### SolarReport (racine)

```python
class SolarReport(BaseModel):
    project_name: str          # Nom du projet
    company_name: str          # Nom de l'entreprise
    report_title: str          # Titre du rapport
    generation_date: date      # Date (auto: aujourd'hui)
    executive_summary: str     # Resume libre (si vide: auto-genere)

    system: SystemConfig
    simulation: SimulationResults
    economics: EconomicAnalysis
    qa: QAReport

    raw_crew_output: str | None  # Texte brut (pour annexes)
```

### SystemConfig

| Champ | Type | Defaut | Description |
|-------|------|--------|-------------|
| `panel_brand` | str | JA Solar | Marque du panneau |
| `panel_model` | str | JAM72S30-545/MR | Modele du panneau |
| `panel_power_wc` | int | 545 | Puissance unitaire (Wc) |
| `panel_efficiency` | float | 0.211 | Rendement du panneau |
| `panel_count` | int | 1 | Nombre de panneaux |
| `total_power_kwc` | float | 0.0 | Puissance totale (kWc) |
| `location_name` | str | Dakar, Senegal | Nom du site |
| `latitude` | float | 14.6928 | Latitude |
| `longitude` | float | -17.4467 | Longitude |
| `altitude` | float | 22 | Altitude (m) |
| `orientation_azimuth` | float | 180.0 | Azimut (0=Nord, 180=Sud) |
| `tilt` | float | 15.0 | Inclinaison (degres) |

### SimulationResults

| Champ | Type | Defaut | Description |
|-------|------|--------|-------------|
| `annual_production_kwh` | float | 0.0 | Production annuelle (kWh) |
| `monthly_production_kwh` | list[float] | [0]*12 | Production par mois (12 valeurs) |
| `specific_yield_kwh_kwc` | float | 0.0 | Rendement specifique (kWh/kWc) |
| `performance_ratio` | float | 0.0 | PR (entre 0 et 1) |
| `soiling_loss_pct` | float | 2.0 | Pertes salissure (%) |
| `mismatch_loss_pct` | float | 1.0 | Pertes mismatch (%) |
| `wiring_loss_pct` | float | 1.5 | Pertes cablage (%) |
| `availability_loss_pct` | float | 1.0 | Pertes disponibilite (%) |
| `temperature_loss_pct` | float | 3.0 | Pertes temperature (%) |
| `total_losses_pct` | float | 0.0 | Pertes totales (%) |

### EconomicAnalysis

| Champ | Type | Defaut | Description |
|-------|------|--------|-------------|
| `total_cost_xof` | float | 0.0 | Cout total (XOF) |
| `cost_per_kwc_xof` | float | 650 000 | Cout par kWc (XOF) |
| `lcoe_xof_kwh` | float | 0.0 | Cout actualise de l'energie |
| `roi_pct` | float | 0.0 | Retour sur investissement (%) |
| `payback_years` | float | 0.0 | Temps de retour (annees) |
| `npv_xof` | float | 0.0 | Valeur actuelle nette (XOF) |
| `annual_savings_xof` | float | 0.0 | Economie annuelle (XOF) |
| `cashflow_cumulative` | list[float] | [0]*25 | Cashflow cumule (25 valeurs) |
| `currency` | str | XOF | Devise |

### QAValidation

| Champ | Type | Description |
|-------|------|-------------|
| `code` | str | Code (V1, V2, EC1, EC2...) |
| `label` | str | Description du critere |
| `status` | str | `PASS`, `FAIL` ou `WARNING` |
| `detail` | str | Details supplementaires |

### QAReport

| Champ | Type | Description |
|-------|------|-------------|
| `validations` | list[QAValidation] | Matrice V1-V10 |
| `edge_cases` | list[QAValidation] | Cas limites EC1-EC6 |
| `verdict` | str | `PASS` ou `FAIL` |
| `notes` | str | Notes supplementaires |

---

## 6. Parseur de sortie CrewAI

Le module `solarintel/reports/parser.py` convertit la sortie texte brut de `crew.kickoff()` en objet `SolarReport`.

### Strategie de parsing (3 niveaux)

```
Sortie CrewAI
     |
     v
[1] Recherche bloc ```json ... ```  ── trouve ──> Construction JSON directe
     |
     | (pas de JSON)
     v
[2] Recherche objet JSON brut {}    ── trouve ──> Construction JSON directe
     |
     | (pas de JSON)
     v
[3] Extraction regex des valeurs    ── toujours ──> Construction par defaut
```

### Patterns regex reconnus (niveau 3)

Le parseur cherche ces motifs dans le texte brut :

| Pattern | Exemple reconnu |
|---------|-----------------|
| `production annuelle : 16350 kWh` | Nombre apres "production annuelle" |
| `Performance Ratio : 82%` | Nombre apres "performance ratio" ou "PR" |
| `LCOE : 52.3` | Nombre apres "LCOE" |
| `cout total : 7 085 000` | Nombre apres "cout total" |
| `ROI : 127%` | Nombre apres "ROI" |
| `payback : 8.2 ans` | Nombre apres "payback" ou "retour" |
| `nombre de panneaux : 20` | Nombre apres "panneaux" |

### Utilisation directe

```python
from solarintel.reports.parser import parse_crew_output

# Depuis la sortie CrewAI
report = parse_crew_output(str(crew_result), project=project_overrides)

# Les champs non trouves gardent les valeurs par defaut de constants.py
print(report.simulation.annual_production_kwh)
print(report.economics.payback_years)
```

### Format JSON attendu (optimal)

Pour de meilleurs resultats, la sortie CrewAI devrait contenir un bloc JSON :

```json
{
  "project_name": "Mon Projet",
  "executive_summary": "Resume du projet...",
  "system": {
    "panel_brand": "JA Solar",
    "panel_count": 20,
    "total_power_kwc": 10.9,
    "latitude": 14.6928,
    "longitude": -17.4467,
    "location_name": "Dakar"
  },
  "simulation": {
    "annual_production_kwh": 16350,
    "monthly_production_kwh": [1050, 1150, ...],
    "performance_ratio": 0.82,
    "specific_yield_kwh_kwc": 1500
  },
  "economics": {
    "total_cost_xof": 7085000,
    "lcoe_xof_kwh": 52.3,
    "payback_years": 8.2,
    "roi_pct": 127,
    "cashflow_cumulative": [-7085000, -5155700, ...]
  },
  "qa": {
    "validations": [
      {"code": "V1", "label": "Puissance crete", "status": "PASS", "detail": "OK"}
    ],
    "edge_cases": [
      {"code": "EC1", "label": "Panneau 0W", "status": "PASS", "detail": "OK"}
    ],
    "verdict": "PASS"
  }
}
```

---

## 7. Personnalisation du theme

Le theme est defini dans `solarintel/reports/theme.py` via la classe `ReportTheme`.

### Palette de couleurs

| Variable | Hex | Utilisation |
|----------|-----|-------------|
| `PRIMARY` | #0EA5E9 | Barres du graphique, KPIs |
| `PRIMARY_DARK` | #0369A1 | Titres, en-tetes tableau, couverture |
| `ACCENT` | #F59E0B | Ligne cashflow (ambre solaire) |
| `SUCCESS` | #22C55E | Statut PASS (vert) |
| `ERROR` | #EF4444 | Statut FAIL (rouge) |
| `WARNING` | #F97316 | Statut WARNING (orange) |
| `BACKGROUND` | #FFFFFF | Fond page (blanc impression) |
| `SURFACE` | #F8FAFC | Fond KPIs |
| `SURFACE_ALT` | #F1F5F9 | Lignes alternees tableaux |
| `TEXT` | #0F172A | Texte principal |
| `TEXT_SECONDARY` | #475569 | Texte secondaire |
| `BORDER` | #CBD5E1 | Bordures, separateurs |

### Polices

| Usage | Police | Built-in ReportLab |
|-------|--------|--------------------|
| Texte general | Helvetica | Oui |
| Titres, gras | Helvetica-Bold | Oui |
| Code, donnees | Courier | Oui |

### Personnaliser les couleurs

Pour modifier le theme, editez `solarintel/reports/theme.py` :

```python
class ReportTheme:
    PRIMARY: Color = HexColor("#1D4ED8")        # Bleu plus fonce
    ACCENT: Color = HexColor("#DC2626")         # Rouge au lieu d'ambre
    COVER_BG: Color = HexColor("#111827")       # Couverture noire
```

### Styles de paragraphe disponibles

| Cle | Taille | Usage |
|-----|--------|-------|
| `title` | 24pt | Titre principal |
| `heading1` | 16pt | Sections (1. Resume, 2. Config...) |
| `heading2` | 13pt | Sous-sections (2.1 Panneaux...) |
| `body` | 10pt | Texte courant (justifie) |
| `body_small` | 8pt | Texte secondaire |
| `mono` | 8pt | Code / donnees brutes |
| `cover_title` | 32pt | Titre page de garde |
| `cover_subtitle` | 16pt | Sous-titre page de garde |
| `kpi_value` | 20pt | Valeurs KPI |
| `kpi_label` | 9pt | Labels KPI |
| `table_header` | 9pt | En-tetes tableau |
| `table_cell` | 9pt | Cellules tableau |

---

## 8. Graphiques

Le module `solarintel/reports/charts.py` genere des graphiques vectoriels integres au PDF.

### Production mensuelle (barres)

```python
from solarintel.reports.charts import build_monthly_production_chart

chart = build_monthly_production_chart(
    monthly_kwh=[1050, 1150, 1450, 1500, 1600, 1550,
                 1400, 1350, 1300, 1250, 1100, 1050],
    width=170 * mm,   # largeur (defaut: 170mm)
    height=100 * mm,  # hauteur (defaut: 100mm)
)
```

- 12 barres (Jan a Dec) en Solar Blue (#0EA5E9)
- Axe Y en kWh avec echelle auto-ajustee
- Labels mois en francais

### Cashflow cumule (ligne)

```python
from solarintel.reports.charts import build_cashflow_chart

chart = build_cashflow_chart(
    cashflow_cumulative=[-7085000 + i * 1929300 for i in range(25)],
    width=170 * mm,
    height=100 * mm,
)
```

- Ligne Amber (#F59E0B) sur 25 ans
- Axe X : annees (affichees tous les 5 ans)
- Axe Y : montant en XOF
- Le point de croisement avec 0 = temps de retour

---

## 9. Logo personnalise

### Logo par defaut

Un logo placeholder est fourni dans `assets/logo_solarintel.png` (soleil stylise + "SI").

### Utiliser votre propre logo

**Via CLI :**

```bash
python main.py --generate-report --logo /chemin/vers/mon_logo.png
```

**Via API Python :**

```python
gen = ReportGenerator(report, logo_path="/chemin/vers/mon_logo.png")
```

### Specifications recommandees

| Parametre | Recommandation |
|-----------|----------------|
| Format | PNG (avec transparence) ou JPG |
| Taille minimale | 400x400 px |
| Ratio | Carre (1:1) de preference |
| Fond | Transparent recommande |

Le logo apparait a deux endroits :
1. **Page de garde** : 50x50 mm, centre
2. **En-tete** : 10x10 mm, en haut a gauche

---

## 10. Exemples complets

### Exemple 1 : Rapport avec donnees minimales

```python
from solarintel.reports import SolarReport, ReportGenerator

report = SolarReport(
    project_name="Test rapide",
    company_name="Ma Societe",
)

gen = ReportGenerator(report)
gen.generate("rapport_minimal.pdf")
```

Le rapport sera genere avec toutes les valeurs par defaut (0 pour les donnees numeriques).

### Exemple 2 : Parser une sortie CrewAI reelle

```python
from solarintel.reports import parse_crew_output, ReportGenerator

# Supposons que crew_output est le resultat de crew.kickoff()
crew_output = """
Analyse terminee.

Production annuelle : 16 350 kWh
Performance Ratio : 82%
LCOE : 52.3 XOF/kWh
Cout total : 7 085 000 XOF
ROI : 127%
Payback : 8.2 ans
Nombre de panneaux : 20
"""

report = parse_crew_output(crew_output)
gen = ReportGenerator(report, logo_path="assets/logo_solarintel.png")
gen.generate("rapport_crew.pdf")
```

### Exemple 3 : Personnaliser le resume executif

```python
report = SolarReport(
    executive_summary=(
        "Ce projet vise l'installation de 20 panneaux JA Solar 545 Wc "
        "sur le toit du batiment administratif de Dakar. L'etude montre "
        "une rentabilite atteinte en 8 ans avec un LCOE 2x inferieur "
        "au tarif SENELEC actuel."
    ),
    # ... autres champs
)
```

Si `executive_summary` est vide (par defaut), le generateur cree automatiquement un resume a partir des donnees du rapport.

### Exemple 4 : Integration dans un script automatise

```python
#!/usr/bin/env python3
"""Script de generation batch de rapports."""

import sys
from solarintel.reports import *

SITES = [
    {"name": "Dakar", "lat": 14.69, "lon": -17.45},
    {"name": "Thies", "lat": 14.79, "lon": -16.93},
    {"name": "Saint-Louis", "lat": 16.02, "lon": -16.50},
]

for site in SITES:
    report = SolarReport(
        project_name=f"PV {site['name']}",
        system=SystemConfig(
            location_name=site["name"],
            latitude=site["lat"],
            longitude=site["lon"],
        ),
    )

    gen = ReportGenerator(report, logo_path="assets/logo_solarintel.png")
    gen.generate(f"rapport_{site['name'].lower()}.pdf")
    print(f"Genere : rapport_{site['name'].lower()}.pdf")
```

---

## 11. Depannage

### Le PDF est vide / pas de donnees

Les modeles utilisent des valeurs par defaut a 0. Assurez-vous de passer des donnees reelles :

```python
simulation = SimulationResults(
    annual_production_kwh=16350,  # NE PAS laisser a 0
    monthly_production_kwh=[...],  # 12 valeurs > 0
)
```

### Le logo n'apparait pas

1. Verifiez que le fichier existe : `ls assets/logo_solarintel.png`
2. Verifiez le chemin passe a `--logo` (absolu ou relatif au repertoire d'execution)
3. Formats supportes : PNG, JPG, GIF

### Erreur `ModuleNotFoundError: reportlab`

```bash
pip install reportlab>=4.0.0
```

### Erreur d'encodage / caracteres speciaux

ReportLab utilise XML en interne. Les caracteres `<`, `>`, `&` dans le texte brut sont automatiquement echappes dans la section Annexes. Si vous injectez du texte dans `executive_summary`, evitez ces caracteres ou utilisez les entites HTML (`&lt;`, `&gt;`, `&amp;`).

### Le graphique cashflow est plat

Verifiez que `cashflow_cumulative` contient des valeurs variees (pas tous des 0) :

```python
economics = EconomicAnalysis(
    cashflow_cumulative=[-7085000 + i * 1929300 for i in range(25)],
)
```

### Modifier les dimensions de page

Par defaut, le rapport utilise A4 (210x297 mm). Pour changer :

```python
# Dans generator.py, remplacer :
from reportlab.lib.pagesizes import A4
# Par :
from reportlab.lib.pagesizes import LETTER
```

### Augmenter/reduire les marges

Editez `solarintel/reports/theme.py` :

```python
class ReportTheme:
    PAGE_MARGIN: float = 25 * mm    # Augmenter (defaut: 20mm)
    HEADER_HEIGHT: float = 20 * mm  # Plus d'espace pour l'en-tete
    FOOTER_HEIGHT: float = 15 * mm  # Plus d'espace pour le pied
```
