"""
SolarIntel — Point d'entrée principal.

Usage :
    python main.py
    python main.py --model codellama --verbose
    python main.py --lat 14.69 --lon -17.45 --panel-power 545
    python main.py --brief-only backend --generate-report
    python main.py --generate-report --logo assets/logo_solarintel.png --company-name "MonEntreprise"
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from solarintel.config.constants import (
    DEFAULT_LOCATION,
    DEFAULT_PANEL,
    ECONOMIC_DEFAULTS,
)
from solarintel.crew import build_solar_crew
from solarintel.tasks.sprint_brief import generate_sprint_brief


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SolarIntel — Pipeline de dimensionnement solaire intelligent"
    )
    parser.add_argument(
        "--model", default=None,
        help="Modèle Ollama à utiliser (défaut: mistral)",
    )
    parser.add_argument(
        "--verbose", action="store_true", default=True,
        help="Activer les logs détaillés",
    )
    parser.add_argument(
        "--brief-only", choices=["frontend", "backend", "qa"],
        help="Générer uniquement le brief pour un agent (sans exécuter la crew)",
    )
    parser.add_argument(
        "--lat", type=float, default=None,
        help="Latitude du site",
    )
    parser.add_argument(
        "--lon", type=float, default=None,
        help="Longitude du site",
    )
    parser.add_argument(
        "--panel-power", type=int, default=None,
        help="Puissance du panneau en Wc",
    )
    parser.add_argument(
        "--consumption-kwh", type=float, default=None,
        help="Consommation annuelle en kWh",
    )
    # -- Report generation args --
    parser.add_argument(
        "--generate-report", action="store_true", default=False,
        help="Générer un rapport PDF après l'exécution",
    )
    parser.add_argument(
        "--logo", type=str, default=None,
        help="Chemin vers le logo à utiliser dans le rapport (défaut: assets/logo_solarintel.png)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=".",
        help="Répertoire de sortie pour le rapport PDF",
    )
    parser.add_argument(
        "--company-name", type=str, default=None,
        help="Nom de l'entreprise pour le rapport",
    )
    parser.add_argument(
        "--report-title", type=str, default=None,
        help="Titre du rapport PDF",
    )
    return parser.parse_args()


def build_project_override(args: argparse.Namespace) -> dict | None:
    """Construit un dict de surcharges projet à partir des arguments CLI."""
    project = {}

    if args.lat is not None or args.lon is not None:
        location = dict(DEFAULT_LOCATION)
        if args.lat is not None:
            location["latitude"] = args.lat
        if args.lon is not None:
            location["longitude"] = args.lon
        project["location"] = location

    if args.panel_power is not None:
        panel = dict(DEFAULT_PANEL)
        panel["power_wc"] = args.panel_power
        project["panel"] = panel

    return project if project else None


def _resolve_logo(args: argparse.Namespace) -> str | None:
    """Résout le chemin du logo."""
    if args.logo:
        return args.logo
    # Default logo path relative to this file
    default = os.path.join(os.path.dirname(__file__), "assets", "logo_solarintel.png")
    if os.path.isfile(default):
        return default
    return None


def _generate_report(
    raw_output: str,
    project: dict | None,
    args: argparse.Namespace,
) -> None:
    """Parse la sortie CrewAI et génère le rapport PDF."""
    # Lazy imports to avoid loading ReportLab when not needed
    from solarintel.reports.parser import parse_crew_output
    from solarintel.reports.generator import ReportGenerator

    report = parse_crew_output(raw_output, project)

    if args.company_name:
        report.company_name = args.company_name
    if args.report_title:
        report.report_title = args.report_title

    logo_path = _resolve_logo(args)
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, "rapport_solarintel.pdf")

    gen = ReportGenerator(
        report=report,
        logo_path=logo_path,
        company_name=args.company_name,
    )
    pdf_path = gen.generate(output_path)

    print()
    print("=" * 70)
    print(f"  RAPPORT PDF généré : {pdf_path}")
    print("=" * 70)


def main() -> None:
    args = parse_args()
    project = build_project_override(args)

    # -- Mode brief-only : affiche le brief sans lancer la crew ------------
    if args.brief_only:
        brief = generate_sprint_brief(args.brief_only, project)
        print(brief)

        if args.generate_report:
            _generate_report(brief, project, args)
        return

    # -- Mode complet : lance la crew CrewAI --------------------------------
    print("=" * 70)
    print("  SOLARINTEL — Pipeline de dimensionnement solaire intelligent")
    print("=" * 70)
    print()

    crew = build_solar_crew(
        llm=args.model,
        project=project,
        verbose=args.verbose,
    )

    result = crew.kickoff()

    print()
    print("=" * 70)
    print("  RÉSULTAT FINAL")
    print("=" * 70)
    print(result)

    if args.generate_report:
        _generate_report(str(result), project, args)


if __name__ == "__main__":
    main()
