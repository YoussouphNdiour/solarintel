"""
SolarIntel — Module de génération de rapports PDF.
"""

from .models import (
    EconomicAnalysis,
    QAReport,
    QAValidation,
    SimulationResults,
    SolarReport,
    SystemConfig,
)
from .generator import ReportGenerator
from .parser import parse_crew_output

__all__ = [
    "EconomicAnalysis",
    "QAReport",
    "QAValidation",
    "ReportGenerator",
    "SimulationResults",
    "SolarReport",
    "SystemConfig",
    "parse_crew_output",
]
