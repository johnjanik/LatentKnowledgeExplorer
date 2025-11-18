"""
Latent Knowledge Explorer (LKE)

A system for extracting structured scientific understanding from Large Language Models.
"""

__version__ = "0.1.0"
__author__ = "LKE Team"

from .core.domain import DomainConfig
from .core.models import StructuredModel, Concept, Relationship
from .interfaces.llm_interface import LLMInterface
from .core.interrogator import InterrogationEngine
from .extractors.structure_extractor import StructureExtractor
from .evaluators.evaluator import Evaluator

__all__ = [
    "DomainConfig",
    "StructuredModel",
    "Concept",
    "Relationship",
    "LLMInterface",
    "InterrogationEngine",
    "StructureExtractor",
    "Evaluator"
]