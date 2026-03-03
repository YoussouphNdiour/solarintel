"""
generate_sprint_brief() – Le cœur du SolarProjectManager.

Génère un prompt structuré et ultra-précis que le Manager envoie
à chaque agent subordonné via CrewAI. Ce brief est le « contrat »
entre le Manager et ses développeurs.
"""

from __future__ import annotations

from textwrap import dedent

from solarintel.config.constants import (
    ARCGIS_BASEMAPS,
    ARCGIS_MODULES,
    DEFAULT_LOCATION,
    DEFAULT_PANEL,
    ECONOMIC_DEFAULTS,
    PVLIB_MODULES,
    UI_THEME,
)


# ═══════════════════════════════════════════════════════════════════════════
# BRIEF FRONTEND
# ═══════════════════════════════════════════════════════════════════════════

def _build_frontend_brief(project: dict | None = None) -> str:
    p = project or {}
    panel = p.get("panel", DEFAULT_PANEL)
    loc = p.get("location", DEFAULT_LOCATION)
    econ = p.get("economics", ECONOMIC_DEFAULTS)
    theme = UI_THEME

    return dedent(f"""\
    ╔══════════════════════════════════════════════════════════════════╗
    ║  SPRINT BRIEF — FRONTEND SOLAR ENGINEER                        ║
    ║  Projet : SolarIntel — Plateforme de dimensionnement PV         ║
    ╚══════════════════════════════════════════════════════════════════╝

    ── 1. ARCHITECTURE UI ──────────────────────────────────────────────

    Layout : Split-screen 50/50 horizontal (responsive → stack vertical < 1024px).

    ┌─────────────────────────┬─────────────────────────────────────────┐
    │     LEFT PANEL (50%)    │          RIGHT PANEL (50%)              │
    │                         │                                         │
    │  Formulaire de saisie   │  Carte ArcGIS interactive               │
    │  + Bilan économique     │  + SketchWidget                         │
    │  + Résultats production │  + Calpinage automatique                │
    └─────────────────────────┴─────────────────────────────────────────┘

    ── 2. LEFT PANEL — Formulaire de saisie ────────────────────────────

    Sections du formulaire (composants Shadcn/UI) :

    A) Configuration Panneau :
       - Select « Marque » : dropdown (défaut: {panel['brand']})
       - Select « Modèle / Type » : dropdown lié à la marque
       - Affichage auto : Puissance {panel['power_wc']}Wc,
         Dimensions {panel['width_mm']}×{panel['height_mm']}mm,
         Rendement {panel['efficiency']*100:.1f}%

    B) Consommation Électrique :
       - Input « Consommation mensuelle » (kWh/mois) — type number
       - Input « Consommation annuelle » (kWh/an) — auto-calculé
       - Input « Prix du kWh » — défaut {econ['electricity_price_kwh']} {econ['currency']}/kWh
       - Input « Augmentation annuelle » — défaut {econ['annual_increase_pct']}%

    C) Paramètres de Calpinage :
       - Input « Espacement horizontal » (cm) — défaut 2
       - Input « Espacement vertical » (cm) — défaut 5
       - Input « Nombre de rangées » — défaut auto
       - Select « Orientation » : Portrait / Paysage
       - ★ BOUTON « Générer le Calpinage Automatique » — style primaire,
         icône soleil, déclenche l'algorithme de placement

    D) Bilan de Production (lecture seule, mis à jour dynamiquement) :
       - Nombre de panneaux placés
       - Puissance crête installée (kWc)
       - Production annuelle estimée (kWh/an)
       - Taux de couverture (%)
       - Économie annuelle ({econ['currency']})
       - Temps de retour sur investissement (années)
       - LCOE ({econ['currency']}/kWh)

    ── 3. RIGHT PANEL — Carte ArcGIS ──────────────────────────────────

    Modules ArcGIS JS SDK à charger :
    {chr(10).join(f'    - {m}' for m in ARCGIS_MODULES)}

    Configuration initiale :
       - Centre : [{loc['latitude']}, {loc['longitude']}]
       - Zoom : 18 (niveau toiture)
       - Basemap toggle :
         • Orthophoto (satellite) : "{ARCGIS_BASEMAPS['orthophoto']}"
         • Topo : "{ARCGIS_BASEMAPS['topo']}"

    SketchWidget :
       - Outil actif par défaut : « polygon »
       - Events à écouter : "create", "update", "delete"
       - À chaque "create-complete" ou "update-complete" :
         1. Extraire les vertices du polygone (geometry.rings)
         2. Calculer la surface via geometryEngine.geodesicArea(polygon, "square-meters")
         3. Émettre un event « polygon-updated » avec {{ rings, area_m2, centroid }}
         4. Déclencher le recalcul du bilan (Left Panel section D)

    ── 4. ALGORITHME DE CALPINAGE ──────────────────────────────────────

    Quand le bouton « Générer le Calpinage Automatique » est cliqué :

    1. Récupérer le polygone actif depuis le GraphicsLayer
    2. Calculer la bounding box orientée (minimum rotated rectangle)
    3. Générer une grille de panneaux :
       - Largeur cellule = panel_width + espacement_h
       - Hauteur cellule = panel_height + espacement_v
       - Orientation selon le choix Portrait/Paysage
    4. Pour chaque cellule de la grille :
       - Vérifier l'inclusion via geometryEngine.contains(polygon, panelRect)
       - Si inclus → ajouter un Graphic (SimpleFillSymbol, couleur {theme['primary']}40)
    5. Compter les panneaux placés → mettre à jour Left Panel
    6. Afficher les panneaux avec :
       - Remplissage : {theme['primary']} à 25% opacité
       - Bordure : {theme['primary']} à 80% opacité, 1px
       - Label central : numéro du panneau (police {theme['font_mono']})

    ── 5. INTÉGRATION RÉACTIVE (CRITIQUE) ──────────────────────────────

    Le state doit être partagé via un store réactif (Zustand / Context) :

    SolarProjectState {{
      polygon: Polygon | null,
      polygonArea_m2: number,
      panelConfig: PanelConfig,
      spacingH_cm: number,
      spacingV_cm: number,
      orientation: "portrait" | "landscape",
      placedPanels: PanelPlacement[],
      panelCount: number,
      peakPower_kWc: number,
      // ... résultats backend
      annualProduction_kWh: number | null,
      economicAnalysis: EconomicResult | null,
    }}

    FLUX DE DONNÉES :
      Carte (dessin) → polygon-updated → recalcul calpinage → count →
      → appel backend pvlib → résultats → mise à jour Left Panel

    Chaque modification sur la carte doit IMMÉDIATEMENT se refléter
    dans le panneau gauche. Zéro action manuelle de synchronisation.

    ── 6. CONTRAINTES DE STYLE ─────────────────────────────────────────

    Framework : {theme['framework']}
    Fond principal : {theme['background']}
    Surface cards : {theme['surface']}
    Bordures : {theme['border']}
    Texte : {theme['text']}
    Accent primaire (Solar Blue) : {theme['primary']}
    Accent énergie : {theme['accent']}
    Police code/données : {theme['font_mono']}
    Police UI : {theme['font_sans']}

    Les composants doivent avoir un look « Engineering dashboard » :
    - Cards avec bordure fine {theme['border']}
    - Inputs avec fond {theme['surface']}, bordure au focus {theme['primary']}
    - Bouton primaire : bg {theme['primary']}, hover {theme['primary_dark']}
    - Données numériques en {theme['font_mono']}
    - Icônes : Lucide React

    ── 7. CRITÈRES D'ACCEPTANCE ────────────────────────────────────────

    ✅ L'interface split-screen se charge sans erreur
    ✅ Le formulaire contient toutes les sections (A, B, C, D)
    ✅ La carte ArcGIS s'affiche avec la basemap satellite
    ✅ Le SketchWidget permet de dessiner des polygones
    ✅ Le bouton « Générer le Calpinage » place les panneaux dans le polygone
    ✅ Le bilan (Left Panel) se met à jour dynamiquement après chaque dessin
    ✅ Le toggle Orthophoto/Topo fonctionne
    ✅ Le responsive < 1024px stack les panels verticalement
    """)


# ═══════════════════════════════════════════════════════════════════════════
# BRIEF BACKEND
# ═══════════════════════════════════════════════════════════════════════════

def _build_backend_brief(project: dict | None = None) -> str:
    p = project or {}
    panel = p.get("panel", DEFAULT_PANEL)
    loc = p.get("location", DEFAULT_LOCATION)
    econ = p.get("economics", ECONOMIC_DEFAULTS)

    return dedent(f"""\
    ╔══════════════════════════════════════════════════════════════════╗
    ║  SPRINT BRIEF — BACKEND PV SIMULATION ENGINEER                  ║
    ║  Projet : SolarIntel — Moteur de simulation pvlib               ║
    ╚══════════════════════════════════════════════════════════════════╝

    ── 1. OBJECTIF ─────────────────────────────────────────────────────

    Transformer les coordonnées du polygone ArcGIS et le nombre de
    panneaux placés en données de production réelle (kWh/an) en
    utilisant pvlib-python.

    ── 2. MODULES PVLIB REQUIS ─────────────────────────────────────────

    {chr(10).join(f'    - {m}' for m in PVLIB_MODULES)}

    ── 3. PIPELINE DE SIMULATION ───────────────────────────────────────

    ÉTAPE 1 — Géolocalisation :
        from pvlib.location import Location

        site = Location(
            latitude=<centroid.lat>,   # depuis le polygone ArcGIS
            longitude=<centroid.lon>,  # depuis le polygone ArcGIS
            altitude={loc['altitude']},
            tz="{loc['timezone']}",
            name="{loc['name']}"
        )

    ÉTAPE 2 — Données météo TMY :
        from pvlib.iotools import get_pvgis_tmy

        tmy_data, _, _, _ = get_pvgis_tmy(
            latitude=site.latitude,
            longitude=site.longitude,
            outputformat="json",
            usehorizon=True,
            startyear=2005,
            endyear=2020,
        )
        # Colonnes attendues : ghi, dni, dhi, temp_air, wind_speed

    ÉTAPE 3 — Définition du système PV :
        from pvlib.pvsystem import PVSystem
        from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

        temp_params = TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

        system = PVSystem(
            surface_tilt=site.latitude,     # inclinaison = latitude (optimal)
            surface_azimuth=180,             # plein sud (hémisphère nord)
            module_parameters={{
                "pdc0": {panel['power_wc']},
                "gamma_pdc": {panel['temp_coeff_pmax'] / 100},
                "b": 0.05,
            }},
            inverter_parameters={{
                "pdc0": {panel['power_wc'] * 1.1},  # surdimensionnement 10%
                "eta_inv_nom": 0.96,
            }},
            temperature_model_parameters=temp_params,
            modules_per_string=<panel_count>,  # depuis le calpinage
            strings_per_inverter=1,
        )

    ÉTAPE 4 — Simulation ModelChain :
        from pvlib.modelchain import ModelChain

        mc = ModelChain(
            system=system,
            location=site,
            aoi_model="physical",
            spectral_model="no_loss",
        )
        mc.run_model(tmy_data)

        # Résultats :
        annual_ac = mc.results.ac.sum()      # Wh/an → convertir en kWh
        annual_dc = mc.results.dc["p_mp"].sum()

    ÉTAPE 5 — Calcul des pertes :
        losses = {{
            "soiling": 0.02,          # 2% encrassement
            "mismatch": 0.02,         # 2% mismatch
            "wiring_dc": 0.02,        # 2% câblage DC
            "wiring_ac": 0.01,        # 1% câblage AC
            "availability": 0.03,     # 3% disponibilité
        }}
        total_loss = 1.0
        for loss in losses.values():
            total_loss *= (1 - loss)

        net_annual_kwh = (annual_ac / 1000) * total_loss

    ── 4. ANALYSE ÉCONOMIQUE ───────────────────────────────────────────

    Paramètres :
        prix_kwh = {econ['electricity_price_kwh']}  # {econ['currency']}/kWh
        augmentation_annuelle = {econ['annual_increase_pct']}%
        durée_vie = {econ['system_lifetime_years']} ans
        dégradation = {econ['degradation_pct_year']}%/an
        coût_wc = {econ['cost_per_wc_xof']} {econ['currency']}/Wc

    Calculs requis :
        - Coût total installation = panel_count × power_wc × coût_wc
        - Économie année N = production_an_N × prix_kwh_an_N
          où production_an_N = net_annual_kwh × (1 - dégradation)^N
          et  prix_kwh_an_N = prix_kwh × (1 + augmentation)^N
        - Flux cumulé → trouver l'année de retour sur investissement
        - LCOE = coût_total / Σ(production sur durée de vie)
        - ROI = (Σ économies - coût_total) / coût_total × 100

    ── 5. FORMAT DE RÉPONSE API ────────────────────────────────────────

    L'endpoint doit retourner :

    {{
        "simulation": {{
            "annual_production_kwh": float,
            "specific_yield_kwh_kwc": float,
            "performance_ratio": float,
            "capacity_factor_pct": float,
            "monthly_production_kwh": [float × 12],
            "losses_breakdown": dict
        }},
        "economics": {{
            "total_cost_xof": int,
            "annual_savings_year1_xof": int,
            "payback_years": float,
            "lcoe_xof_kwh": float,
            "roi_pct": float,
            "npv_25y_xof": int,
            "cashflow_annual": [float × 25]
        }},
        "system": {{
            "panel_count": int,
            "peak_power_kwc": float,
            "panel_brand": str,
            "panel_model": str,
            "tilt_deg": float,
            "azimuth_deg": float,
            "location": {{
                "lat": float,
                "lon": float,
                "name": str
            }}
        }}
    }}

    ── 6. CRITÈRES D'ACCEPTANCE ────────────────────────────────────────

    ✅ pvlib.location.Location est utilisé avec les coordonnées du centroïde
    ✅ pvlib.modelchain.ModelChain simule la chaîne complète
    ✅ Les données TMY sont récupérées via PVGIS
    ✅ Les pertes thermiques sont modélisées (SAPM temperature model)
    ✅ L'analyse économique est en {econ['currency']}
    ✅ Le temps de retour sur investissement est calculé
    ✅ Le LCOE est calculé et retourné
    ✅ Les résultats mensuels sont fournis (pour graphique)
    """)


# ═══════════════════════════════════════════════════════════════════════════
# BRIEF QA
# ═══════════════════════════════════════════════════════════════════════════

def _build_qa_brief(project: dict | None = None) -> str:
    p = project or {}
    panel = p.get("panel", DEFAULT_PANEL)
    econ = p.get("economics", ECONOMIC_DEFAULTS)

    return dedent(f"""\
    ╔══════════════════════════════════════════════════════════════════╗
    ║  SPRINT BRIEF — QA & CROSS-VALIDATION REVIEWER                  ║
    ║  Projet : SolarIntel — Validation croisée Frontend ↔ Backend    ║
    ╚══════════════════════════════════════════════════════════════════╝

    ── 1. OBJECTIF ─────────────────────────────────────────────────────

    Vérifier la COHÉRENCE COMPLÈTE entre :
      - La puissance installée sur la carte (panneaux placés × {panel['power_wc']}Wc)
      - Les besoins calculés dans le bilan de consommation (Left Panel)
      - Les résultats de la simulation pvlib (Backend)

    ── 2. MATRICE DE VALIDATION ────────────────────────────────────────

    ┌────┬────────────────────────────────────────┬──────────┬────────┐
    │ #  │ Point de contrôle                      │ Source   │ Verdict│
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V1 │ Surface polygone ArcGIS (m²) ≈         │ Frontend │ ?/FAIL │
    │    │ surface calculée par geometryEngine     │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V2 │ Nb panneaux placés × dimensions =      │ Frontend │ ?/FAIL │
    │    │ surface occupée ≤ surface polygone      │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V3 │ Puissance installée (kWc) =            │ F+B      │ ?/FAIL │
    │    │ nb_panneaux × {panel['power_wc']}Wc / 1000         │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V4 │ Production pvlib (kWh/an) est dans     │ Backend  │ ?/FAIL │
    │    │ la plage [1200-1800 kWh/kWc] pour      │          │        │
    │    │ l'Afrique de l'Ouest                   │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V5 │ Taux de couverture (%) =               │ F+B      │ ?/FAIL │
    │    │ production / consommation × 100         │          │        │
    │    │ Cohérent avec la taille du système      │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V6 │ LCOE calculé est dans la plage         │ Backend  │ ?/FAIL │
    │    │ [50 - 150] {econ['currency']}/kWh                  │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V7 │ Le dessin d'un nouveau polygone         │ Integ.   │ ?/FAIL │
    │    │ déclenche automatiquement le recalcul   │          │        │
    │    │ du bilan dans le Left Panel             │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V8 │ La suppression du polygone reset        │ Integ.   │ ?/FAIL │
    │    │ tous les champs du bilan à 0/null       │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │ V9 │ Les coordonnées envoyées au backend     │ Integ.   │ ?/FAIL │
    │    │ correspondent au centroïde du polygone  │          │        │
    ├────┼────────────────────────────────────────┼──────────┼────────┤
    │V10 │ Polygone non-convexe : l'algorithme     │ Frontend │ ?/FAIL │
    │    │ de calpinage ne place PAS de panneaux   │          │        │
    │    │ en dehors des limites                   │          │        │
    └────┴────────────────────────────────────────┴──────────┴────────┘

    ── 3. TESTS EDGE CASES ─────────────────────────────────────────────

    EC1 : Polygone très petit (< 5m²) → message "Surface insuffisante"
    EC2 : Polygone très grand (> 10000m²) → avertissement performance
    EC3 : Espacement = 0 cm → les panneaux se touchent (valide)
    EC4 : Consommation = 0 kWh → le taux de couverture = ∞ → afficher "N/A"
    EC5 : Coordonnées hors zone de couverture PVGIS → erreur gracieuse
    EC6 : Changement de panneau après calpinage → recalcul automatique

    ── 4. FORMAT DU RAPPORT ────────────────────────────────────────────

    Produire un rapport structuré :

    ```
    ══════════════════════════════════════
    RAPPORT DE VALIDATION — SolarIntel
    Date : {{date}}
    ══════════════════════════════════════

    RÉSUMÉ : X/10 PASS | Y/10 FAIL

    DÉTAIL :
    [V1] PASS — Surface polygone = 45.2 m², geometryEngine = 45.18 m² (Δ < 0.1%)
    [V2] FAIL — 12 panneaux × 2.58 m² = 30.96 m² > surface 25 m²
    ...

    EDGE CASES :
    [EC1] PASS — Message affiché correctement
    ...

    RECOMMANDATIONS :
    - ...

    VERDICT GLOBAL : ✅ PASS / ❌ FAIL
    ══════════════════════════════════════
    ```

    ── 5. CRITÈRES D'ACCEPTANCE ────────────────────────────────────────

    ✅ Les 10 points de validation sont évalués
    ✅ Les 6 edge cases sont testés
    ✅ Le rapport est structuré et lisible
    ✅ Les valeurs numériques sont comparées avec des tolérances
    ✅ Le verdict global est clair (PASS/FAIL)
    """)


# ═══════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE PUBLIC
# ═══════════════════════════════════════════════════════════════════════════

def generate_sprint_brief(
    target: str,
    project: dict | None = None,
) -> str:
    """
    Génère un sprint brief structuré pour un agent subordonné.

    Args:
        target: "frontend" | "backend" | "qa"
        project: dict optionnel pour surcharger les defaults
                 (panel, location, economics)

    Returns:
        Le brief formaté prêt à être injecté dans une Task CrewAI.
    """
    builders = {
        "frontend": _build_frontend_brief,
        "backend": _build_backend_brief,
        "qa": _build_qa_brief,
    }

    if target not in builders:
        raise ValueError(
            f"Target invalide '{target}'. "
            f"Valeurs possibles : {list(builders.keys())}"
        )

    return builders[target](project)
