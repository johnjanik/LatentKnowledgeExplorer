"""
Core domain models and interrogation logic.
"""

from .domain import DomainConfig
from .models import StructuredModel, Concept, Relationship, Axiom
from .interrogator import InterrogationEngine

__all__ = [
    "DomainConfig",
    "StructuredModel",
    "Concept",
    "Relationship",
    "Axiom",
    "InterrogationEngine"
]
