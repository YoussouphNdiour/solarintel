# SolarIntel

Pipeline de dimensionnement solaire intelligent propulse par CrewAI.

SolarIntel orchestre une equipe d'agents IA specialises (Frontend, Backend PV, QA) pilotes par un chef de projet pour generer des briefs techniques complets pour le developpement d'une plateforme de dimensionnement photovoltaique.

---

## Table des matieres

- [Architecture](#architecture)
- [Installation](#installation)
- [Demarrage rapide](#demarrage-rapide)
- [Commandes CLI](#commandes-cli)
- [Generation de rapport PDF](#generation-de-rapport-pdf)
- [Structure du projet](#structure-du-projet)
- [Configuration](#configuration)
- [Documentation detaillee](#documentation-detaillee)

---

## Architecture

```
                    +-----------------------+
                    |  Solar Project Manager |
                    |   (Orchestrateur)      |
                    +----------+------------+
                               |
              +----------------+----------------+
              |                |                |
     +--------v------+ +------v--------+ +-----v---------+
     | Frontend Agent | | Backend Agent | |   QA Agent    |
     | ArcGIS + UI   | | pvlib + Eco   | | Validation    |
     +---------------+ +---------------+ +---------------+
              |                |                |
              v                v                v
         Sprint Brief     Sprint Brief     Rapport QA
                    \          |          /
                     v         v         v
                  +------------------------+
                  |   Rapport PDF (opt.)   |
                  |   ReportLab A4         |
                  +------------------------+
```

**Stack technique :**
- **CrewAI** : orchestration multi-agents hierarchique
- **pvlib** : simulation photovoltaique (TMY, ModelChain)
- **Ollama** : LLM local (Mistral par defaut)
- **ReportLab** : generation de rapports PDF professionnels
- **Pydantic** : validation des donnees

---

## Installation

### Pre-requis

- Python 3.10+
- [Ollama](https://ollama.ai) installe et lance (`ollama serve`)
- Un modele telecharge (`ollama pull mistral`)

### Installation des dependances

```bash
cd solarintel
pip install -r requirements.txt
```

### Dependances

| Package | Version | Role |
|---------|---------|------|
| crewai | >= 0.80.0 | Orchestration multi-agents |
| crewai-tools | >= 0.14.0 | Outils pour agents |
| pvlib | >= 0.11.0 | Simulation PV |
| pandas | >= 2.0.0 | Traitement de donnees |
| pydantic | >= 2.0.0 | Validation des modeles |
| langchain-ollama | >= 0.2.0 | Integration LLM local |
| reportlab | >= 4.0.0 | Generation PDF |

---

## Demarrage rapide

### 1. Generer un brief (sans LLM)

```bash
# Brief Backend (simulation pvlib)
python main.py --brief-only backend

# Brief Frontend (ArcGIS + UI)
python main.py --brief-only frontend

# Brief QA (validation croisee)
python main.py --brief-only qa
```

### 2. Lancer le pipeline complet (necessite Ollama)

```bash
python main.py
```

### 3. Generer un rapport PDF

```bash
# Avec brief uniquement
python main.py --brief-only backend --generate-report

# Pipeline complet + rapport
python main.py --generate-report

# Personnalise
python main.py --generate-report \
    --logo mon_logo.png \
    --company-name "MonEntreprise Solaire" \
    --report-title "Etude PV Site Dakar" \
    --output-dir ./rapports
```

---

## Commandes CLI

```
python main.py [OPTIONS]
```

### Options generales

| Option | Type | Defaut | Description |
|--------|------|--------|-------------|
| `--model` | str | mistral | Modele Ollama a utiliser |
| `--verbose` | flag | True | Logs detailles |
| `--brief-only` | choix | - | `frontend`, `backend` ou `qa` |
| `--lat` | float | 14.6928 | Latitude du site |
| `--lon` | float | -17.4467 | Longitude du site |
| `--panel-power` | int | 545 | Puissance du panneau (Wc) |
| `--consumption-kwh` | float | - | Consommation annuelle (kWh) |

### Options rapport PDF

| Option | Type | Defaut | Description |
|--------|------|--------|-------------|
| `--generate-report` | flag | False | Active la generation PDF |
| `--logo` | chemin | `assets/logo_solarintel.png` | Logo personnalise |
| `--output-dir` | chemin | `.` | Repertoire de sortie |
| `--company-name` | str | SolarIntel | Nom de l'entreprise |
| `--report-title` | str | Rapport de Dimensionnement Solaire | Titre du rapport |

---

## Generation de rapport PDF

Le module `solarintel.reports` genere des rapports PDF professionnels au format A4 contenant :

1. **Page de garde** : fond bleu, logo centre, titre, lieu, date
2. **Resume executif** : synthese auto-generee + 4 KPIs visuels
3. **Configuration systeme** : tableaux panneaux + localisation
4. **Simulation pvlib** : KPIs + graphique barres 12 mois + pertes
5. **Analyse economique** : tableau financier + courbe cashflow 25 ans
6. **Rapport QA** : matrice PASS/FAIL coloree + edge cases + verdict
7. **Annexes** : modules pvlib, constantes, formules, methodologie

> Voir le **[Guide complet du rapport PDF](docs/GUIDE_RAPPORT_PDF.md)** pour l'utilisation avancee et l'API Python.

---

## Structure du projet

```
solarintel/
|-- main.py                          # Point d'entree CLI
|-- requirements.txt                 # Dependances Python
|-- assets/
|   +-- logo_solarintel.png          # Logo par defaut
|
+-- solarintel/
    |-- __init__.py
    |-- crew.py                      # Assemblage de la Crew CrewAI
    |
    |-- agents/
    |   |-- __init__.py
    |   |-- manager.py               # Agent Chef de projet
    |   +-- subordinates.py          # Agents Frontend/Backend/QA
    |
    |-- tasks/
    |   |-- __init__.py
    |   |-- definitions.py           # Factory de taches CrewAI
    |   +-- sprint_brief.py          # Generateur de briefs techniques
    |
    |-- config/
    |   |-- __init__.py
    |   +-- constants.py             # Constantes globales (theme, pvlib, eco)
    |
    |-- reports/                     # Module generation PDF
    |   |-- __init__.py              # Re-exports publics
    |   |-- models.py                # Modeles Pydantic (SolarReport, etc.)
    |   |-- theme.py                 # Palette impression (ReportTheme)
    |   |-- charts.py                # Graphiques vectoriels
    |   |-- generator.py             # Moteur PDF (ReportGenerator)
    |   +-- parser.py                # Parseur sortie CrewAI
    |
    +-- tools/
        +-- __init__.py              # (placeholder futur)
```

---

## Configuration

Les valeurs par defaut sont dans `solarintel/config/constants.py` :

### Localisation (Dakar, Senegal)

| Parametre | Valeur |
|-----------|--------|
| Latitude | 14.6928 |
| Longitude | -17.4467 |
| Altitude | 22 m |
| Fuseau | Africa/Dakar |

### Panneau par defaut (JA Solar)

| Parametre | Valeur |
|-----------|--------|
| Modele | JAM72S30-545/MR |
| Puissance | 545 Wc |
| Efficacite | 21.1% |
| Coeff. temp. | -0.350 %/C |

### Economique (Afrique de l'Ouest)

| Parametre | Valeur |
|-----------|--------|
| Devise | XOF (FCFA) |
| Tarif electricite | 118 FCFA/kWh |
| Augmentation annuelle | 3.5% |
| Duree de vie | 25 ans |
| Degradation | 0.5%/an |
| Cout par Wc | 650 FCFA |

---

## Documentation detaillee

- **[Guide rapport PDF](docs/GUIDE_RAPPORT_PDF.md)** : utilisation complete du generateur de rapports, API Python, personnalisation du theme, exemples

---

## Licence

Projet prive SolarIntel.
