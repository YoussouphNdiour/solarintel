"""
Crew SolarIntel – Orchestration du pipeline complet.

Assemble le Manager, les agents subordonnés, et les tasks
en une Crew CrewAI prête à être exécutée.
"""

from __future__ import annotations

from crewai import Crew, LLM, Process

from solarintel.agents.manager import create_solar_project_manager
from solarintel.agents.subordinates import (
    create_backend_agent,
    create_frontend_agent,
    create_qa_agent,
)
from solarintel.config.constants import OLLAMA_BASE_URL, OLLAMA_MODEL
from solarintel.tasks.definitions import (
    create_backend_task,
    create_frontend_task,
    create_qa_task,
)


def _build_ollama_llm(model: str | None = None) -> LLM:
    """Construit un objet LLM CrewAI pointant vers Ollama local."""
    model_name = model or OLLAMA_MODEL
    return LLM(
        model=f"ollama/{model_name}",
        base_url=OLLAMA_BASE_URL,
    )


def build_solar_crew(
    llm: str | None = None,
    project: dict | None = None,
    verbose: bool = True,
) -> Crew:
    """
    Construit et retourne la Crew SolarIntel complète.

    Args:
        llm: identifiant du modèle Ollama (ex: "mistral", "codellama").
             Si None, utilise le défaut de config/constants.py.
        project: dict optionnel pour surcharger les paramètres projet
                 (panel, location, economics).
        verbose: active les logs détaillés.

    Returns:
        Crew prête à être kickoff().
    """
    ollama_llm = _build_ollama_llm(llm)

    # -- Agents ------------------------------------------------------------
    manager = create_solar_project_manager(llm=ollama_llm, verbose=verbose)
    frontend_dev = create_frontend_agent(llm=ollama_llm, verbose=verbose)
    backend_dev = create_backend_agent(llm=ollama_llm, verbose=verbose)
    qa_reviewer = create_qa_agent(llm=ollama_llm, verbose=verbose)

    # -- Tasks (séquentielles : frontend → backend → QA) -------------------
    frontend_task = create_frontend_task(agent=frontend_dev, project=project)
    backend_task = create_backend_task(agent=backend_dev, project=project)
    qa_task = create_qa_task(
        agent=qa_reviewer,
        project=project,
        context=[frontend_task, backend_task],
    )

    # -- Crew --------------------------------------------------------------
    return Crew(
        agents=[frontend_dev, backend_dev, qa_reviewer],
        tasks=[frontend_task, backend_task, qa_task],
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=verbose,
        memory=False,
        max_rpm=10,  # rate limit pour Ollama local
    )
