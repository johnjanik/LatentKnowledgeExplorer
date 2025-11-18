"""
Core data models for the Latent Knowledge Explorer.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from enum import Enum


class RelationshipType(Enum):
    """Types of relationships between concepts."""
    PREREQUISITE = "prerequisite"
    CAUSAL = "causal"
    COMPOSITIONAL = "compositional"
    TEMPORAL = "temporal"
    EQUIVALENCE = "equivalence"
    INHERITANCE = "inheritance"


@dataclass
class Concept:
    """Represents a scientific concept or entity."""
    id: str
    name: str
    definition: str
    properties: Dict[str, Any] = field(default_factory=dict)
    synonyms: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert concept to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "properties": self.properties,
            "synonyms": self.synonyms,
            "examples": self.examples,
            "confidence": self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Concept":
        """Create concept from dictionary."""
        return cls(**data)


@dataclass
class Relationship:
    """Represents a relationship between concepts."""
    source: str  # Concept ID
    target: str  # Concept ID
    type: RelationshipType
    description: Optional[str] = None
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "description": self.description,
            "strength": self.strength,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create relationship from dictionary."""
        data["type"] = RelationshipType(data["type"])
        return cls(**data)


@dataclass
class Axiom:
    """Represents an axiom or fundamental law."""
    id: str
    statement: str
    formal_expression: Optional[str] = None
    concepts_involved: List[str] = field(default_factory=list)
    derivable_theorems: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert axiom to dictionary."""
        return {
            "id": self.id,
            "statement": self.statement,
            "formal_expression": self.formal_expression,
            "concepts_involved": self.concepts_involved,
            "derivable_theorems": self.derivable_theorems,
            "confidence": self.confidence
        }


@dataclass
class StructuredModel:
    """
    Represents an externalized model of a scientific domain extracted from an LLM.
    """
    domain_name: str
    domain_description: str
    concepts: List[Concept]
    relationships: List[Relationship]
    axioms: List[Axiom]
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_date: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate and index the model."""
        self._concept_index = {c.id: c for c in self.concepts}
        self._validate_relationships()

    def _validate_relationships(self):
        """Validate that all relationships reference existing concepts."""
        concept_ids = set(self._concept_index.keys())
        for rel in self.relationships:
            if rel.source not in concept_ids:
                raise ValueError(f"Relationship source '{rel.source}' not found in concepts")
            if rel.target not in concept_ids:
                raise ValueError(f"Relationship target '{rel.target}' not found in concepts")

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self._concept_index.get(concept_id)

    def get_prerequisites(self, concept_id: str) -> List[Concept]:
        """Get prerequisite concepts for a given concept."""
        prereqs = []
        for rel in self.relationships:
            if rel.target == concept_id and rel.type == RelationshipType.PREREQUISITE:
                prereq = self.get_concept(rel.source)
                if prereq:
                    prereqs.append(prereq)
        return prereqs

    def get_dependents(self, concept_id: str) -> List[Concept]:
        """Get concepts that depend on a given concept."""
        deps = []
        for rel in self.relationships:
            if rel.source == concept_id and rel.type == RelationshipType.PREREQUISITE:
                dep = self.get_concept(rel.target)
                if dep:
                    deps.append(dep)
        return deps

    def get_causal_parents(self, concept_id: str) -> List[Concept]:
        """Get causal parents of a concept."""
        parents = []
        for rel in self.relationships:
            if rel.target == concept_id and rel.type == RelationshipType.CAUSAL:
                parent = self.get_concept(rel.source)
                if parent:
                    parents.append(parent)
        return parents

    def get_causal_children(self, concept_id: str) -> List[Concept]:
        """Get causal children of a concept."""
        children = []
        for rel in self.relationships:
            if rel.source == concept_id and rel.type == RelationshipType.CAUSAL:
                child = self.get_concept(rel.target)
                if child:
                    children.append(child)
        return children

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for serialization."""
        return {
            "domain_name": self.domain_name,
            "domain_description": self.domain_description,
            "concepts": [c.to_dict() for c in self.concepts],
            "relationships": [r.to_dict() for r in self.relationships],
            "axioms": [a.to_dict() for a in self.axioms],
            "metadata": self.metadata,
            "extraction_date": self.extraction_date.isoformat()
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert the model to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StructuredModel":
        """Create a model from a dictionary."""
        data["concepts"] = [Concept.from_dict(c) for c in data.get("concepts", [])]
        data["relationships"] = [Relationship.from_dict(r) for r in data.get("relationships", [])]
        data["axioms"] = [Axiom(**a) for a in data.get("axioms", [])]
        data["extraction_date"] = datetime.fromisoformat(data.get("extraction_date", datetime.now().isoformat()))
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "StructuredModel":
        """Create a model from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def get_graph_representation(self) -> Dict[str, List[str]]:
        """Get adjacency list representation of the concept graph."""
        graph = {c.id: [] for c in self.concepts}
        for rel in self.relationships:
            if rel.source in graph:
                graph[rel.source].append(rel.target)
        return graph

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the model."""
        rel_type_counts = {}
        for rel in self.relationships:
            rel_type = rel.type.value
            rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

        return {
            "num_concepts": len(self.concepts),
            "num_relationships": len(self.relationships),
            "num_axioms": len(self.axioms),
            "relationship_types": rel_type_counts,
            "avg_concept_confidence": sum(c.confidence for c in self.concepts) / len(self.concepts) if self.concepts else 0,
            "extraction_date": self.extraction_date.isoformat()
        }