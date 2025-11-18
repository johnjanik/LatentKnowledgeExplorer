"""
Base plugin interface for domain-specific logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class DomainLogicPlugin(ABC):
    """
    Base class for user-implemented domain logic.

    This allows scientists to inject their domain expertise into the extraction process.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize plugin with optional configuration.

        Args:
            config: Domain-specific configuration parameters
        """
        self.config = config or {}

    @abstractmethod
    def preprocess_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform input data to domain-specific format.

        Args:
            data: Raw input data

        Returns:
            Preprocessed data suitable for domain analysis
        """
        pass

    @abstractmethod
    def validate_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """
        Apply domain-specific validation rules to concepts.

        Args:
            concepts: List of extracted concepts

        Returns:
            Validated and potentially corrected concepts
        """
        pass

    @abstractmethod
    def compute_relationships(self, concepts: List[Dict]) -> Dict[str, List[str]]:
        """
        Derive domain-specific relationships between concepts.

        Args:
            concepts: List of validated concepts

        Returns:
            Dictionary mapping concept IDs to related concept IDs
        """
        pass

    @abstractmethod
    def evaluate_consistency(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check model against domain-specific constraints.

        Args:
            model: Complete extracted model

        Returns:
            Dictionary with validation results:
            - 'valid': bool
            - 'errors': List of error messages
            - 'warnings': List of warning messages
            - 'suggestions': List of improvement suggestions
        """
        pass

    def enrich_with_knowledge(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optionally enrich model with additional domain knowledge.

        Args:
            model: Extracted model

        Returns:
            Enriched model with additional information
        """
        return model

    def rank_importance(self, concepts: List[Dict]) -> List[Dict]:
        """
        Optionally rank concepts by domain-specific importance.

        Args:
            concepts: List of concepts

        Returns:
            Concepts with 'importance' scores added
        """
        return concepts

    def suggest_experiments(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Optionally suggest experiments to validate the model.

        Args:
            model: Extracted model

        Returns:
            List of suggested experiments with descriptions
        """
        return []