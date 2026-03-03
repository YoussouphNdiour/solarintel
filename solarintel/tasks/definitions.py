"""
Définitions des Tasks CrewAI pour le pipeline SolarIntel.

Chaque task encapsule un sprint brief généré par le Manager
et l'assigne à l'agent subordonné correspondant.
"""

from __future__ import annotations

from crewai import Agent, Task

from .sprint_brief import generate_sprint_brief


def create_frontend_task(
    agent: Agent,
    project: dict | None = None,
) -> Task:
    """Task pour le Frontend Solar Engineer."""

    brief = generate_sprint_brief("frontend", project)

    return Task(
        description=(
            "Implémente l'interface de dimensionnement solaire selon "
            "le brief suivant. Respecte CHAQUE spécification.\n\n"
            f"{brief}"
        ),
        expected_output=(
            "Code complet de l'interface split-screen comprenant :\n"
            "1. Le composant principal SolarDesigner avec layout 50/50\n"
            "2. Le Left Panel (formulaire + bilan) avec tous les inputs\n"
            "3. Le Right Panel (carte ArcGIS + SketchWidget)\n"
            "4. L'algorithme de calpinage (placement de panneaux)\n"
            "5. Le store réactif partagé entre les deux panels\n"
            "6. Le style complet conforme au thème Engineering"
        ),
        agent=agent,
    )


def create_backend_task(
    agent: Agent,
    project: dict | None = None,
) -> Task:
    """Task pour le Backend PV Simulation Engineer."""

    brief = generate_sprint_brief("backend", project)

    return Task(
        description=(
            "Développe le moteur de simulation PV selon le brief "
            "suivant. Utilise EXACTEMENT les modules pvlib spécifiés.\n\n"
            f"{brief}"
        ),
        expected_output=(
            "Code Python complet du moteur de simulation comprenant :\n"
            "1. Fonction de géolocalisation avec pvlib.location.Location\n"
            "2. Récupération des données TMY via PVGIS\n"
            "3. Configuration PVSystem avec les paramètres du panneau\n"
            "4. Simulation ModelChain complète\n"
            "5. Calcul des pertes (soiling, mismatch, wiring, etc.)\n"
            "6. Analyse économique complète (LCOE, ROI, payback)\n"
            "7. Endpoint API retournant le JSON structuré spécifié"
        ),
        agent=agent,
    )


def create_qa_task(
    agent: Agent,
    project: dict | None = None,
    context: list[Task] | None = None,
) -> Task:
    """Task pour le QA & Cross-Validation Reviewer.

    Le contexte inclut les tasks frontend et backend pour permettre
    la validation croisée.
    """

    brief = generate_sprint_brief("qa", project)

    return Task(
        description=(
            "Effectue la validation croisée Frontend ↔ Backend selon "
            "le brief suivant. Vérifie CHAQUE point de contrôle.\n\n"
            f"{brief}"
        ),
        expected_output=(
            "Rapport de validation structuré comprenant :\n"
            "1. Résumé X/10 PASS | Y/10 FAIL\n"
            "2. Détail de chaque validation (V1–V10) avec valeurs\n"
            "3. Résultat des tests edge cases (EC1–EC6)\n"
            "4. Recommandations correctives si FAIL\n"
            "5. Verdict global PASS ou FAIL"
        ),
        agent=agent,
        context=context or [],
    )
