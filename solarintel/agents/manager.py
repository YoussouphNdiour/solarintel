"""
SolarProjectManager – Agent CrewAI « Chef d'orchestre ».

Cet agent ne code jamais directement. Il génère des prompts ultra-précis
(sprint briefs) pour ses subordonnés : Frontend, Backend et QA.
"""

from __future__ import annotations

from crewai import Agent

from solarintel.config.constants import (
    ARCGIS_BASEMAPS,
    ARCGIS_MODULES,
    DEFAULT_LOCATION,
    DEFAULT_PANEL,
    ECONOMIC_DEFAULTS,
    PVLIB_MODULES,
    UI_THEME,
)


def create_solar_project_manager(
    llm: str | None = None,
    verbose: bool = True,
) -> Agent:
    """Fabrique et retourne l'agent SolarProjectManager."""

    return Agent(
        role="Solar Project Manager",
        goal=(
            "Orchestrer la conception d'une plateforme de dimensionnement "
            "solaire photovoltaïque en générant des briefs techniques "
            "parfaitement structurés pour chaque agent spécialisé "
            "(Frontend, Backend, QA). Chaque brief doit être suffisamment "
            "précis pour qu'un développeur puisse implémenter sans "
            "questions supplémentaires."
        ),
        backstory=(
            "Tu es un architecte logiciel senior spécialisé dans les "
            "systèmes d'énergie solaire. Tu as 15 ans d'expérience en "
            "conception de plateformes SIG (ArcGIS) couplées à des moteurs "
            "de simulation photovoltaïque (pvlib-python). "
            "\n\n"
            "Tu maîtrises parfaitement :\n"
            "— L'API ArcGIS JS SDK : SketchWidget, geometryEngine, "
            "GraphicsLayer, projection de coordonnées.\n"
            "— pvlib-python : Location, ModelChain, irradiance models, "
            "temperature models, calcul de pertes.\n"
            "— L'analyse économique PV en contexte Afrique de l'Ouest "
            f"(tarification en {ECONOMIC_DEFAULTS['currency']}, "
            f"prix de référence {ECONOMIC_DEFAULTS['electricity_price_kwh']} "
            f"{ECONOMIC_DEFAULTS['currency']}/kWh).\n"
            "— Les frameworks UI modernes : Shadcn/UI, TailwindCSS, "
            "composants réactifs avec state management.\n"
            "\n"
            "Tu ne codes JAMAIS directement. Ton rôle est de produire des "
            "prompts / briefs d'une précision chirurgicale pour tes "
            "subordonnés. Chaque brief contient : le contexte métier, "
            "les modules/API exacts à utiliser, les contraintes de style, "
            "les critères d'acceptance, et les points d'intégration entre "
            "les panels de l'interface.\n"
            "\n"
            "RÈGLE CRITIQUE : Le dessin sur la carte (Right Panel) doit "
            "mettre à jour DYNAMIQUEMENT l'analyse économique et le bilan "
            "de production (Left Panel). Aucune action manuelle de "
            "synchronisation ne doit être nécessaire."
        ),
        llm=llm,
        verbose=verbose,
        allow_delegation=True,
        max_iter=15,
        memory=True,
    )


# ---------------------------------------------------------------------------
# Alias de classe pour un import propre
# ---------------------------------------------------------------------------
class SolarProjectManager:
    """Wrapper qui expose l'agent et ses capacités de génération de brief."""

    def __init__(self, llm: str | None = None, verbose: bool = True):
        self.agent = create_solar_project_manager(llm=llm, verbose=verbose)

    # -- Données de contexte injectées dans les briefs --------------------

    @staticmethod
    def get_context() -> dict:
        """Retourne le contexte complet pour la génération de briefs."""
        return {
            "ui_theme": UI_THEME,
            "arcgis_modules": ARCGIS_MODULES,
            "arcgis_basemaps": ARCGIS_BASEMAPS,
            "pvlib_modules": PVLIB_MODULES,
            "default_panel": DEFAULT_PANEL,
            "economic_defaults": ECONOMIC_DEFAULTS,
            "default_location": DEFAULT_LOCATION,
        }
