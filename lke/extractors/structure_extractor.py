"""
Structure extraction module for parsing LLM responses into structured models.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import json

from ..core.models import (
    Concept, Relationship, Axiom, StructuredModel, RelationshipType
)
from ..core.interrogator import InterrogationResult


class StructureExtractor:
    """
    Converts raw textual responses into structured objects.

    Parses LLM outputs and builds graphs, relationships, and formal structures.
    """

    def __init__(self, strict_parsing: bool = False):
        """
        Initialize structure extractor.

        Args:
            strict_parsing: If True, raise errors on parsing failures.
                          If False, attempt best-effort extraction.
        """
        self.strict_parsing = strict_parsing
        self.concept_counter = 0

    def extract_model(self, result: InterrogationResult,
                     domain_name: str,
                     domain_description: str) -> StructuredModel:
        """
        Extract a complete structured model from interrogation results.

        Args:
            result: Raw interrogation results
            domain_name: Name of the domain
            domain_description: Description of the domain

        Returns:
            StructuredModel containing parsed knowledge
        """
        # Extract concepts
        concepts = self.parse_concepts(result.raw_concepts)

        # Build concept index for relationship parsing
        concept_index = {c.name.lower(): c.id for c in concepts}

        # Extract relationships
        prereq_relationships = self.parse_prerequisites(
            result.raw_prerequisites,
            concept_index
        )

        causal_relationships = self.parse_causal_relationships(
            result.raw_causal,
            concept_index
        )

        # Combine relationships
        relationships = prereq_relationships + causal_relationships

        # Extract axioms
        axioms = self.parse_axioms(result.raw_axioms, concept_index)

        return StructuredModel(
            domain_name=domain_name,
            domain_description=domain_description,
            concepts=concepts,
            relationships=relationships,
            axioms=axioms,
            metadata=result.metadata
        )

    def parse_concepts(self, raw_concepts: str) -> List[Concept]:
        """
        Parse concepts from raw text.

        Expected formats:
        - Numbered list: "1. Name: definition"
        - Bullet list: "- Name: definition"
        - Structured: "Name\nDefinition: ...\nProperties: ...\nExamples: ..."
        """
        concepts = []

        # Try numbered list format first
        numbered_pattern = r'(\d+)\.\s*([^:]+):\s*([^\n]+(?:\n(?!\d+\.)[^\n]+)*)'
        matches = re.findall(numbered_pattern, raw_concepts, re.MULTILINE)

        if matches:
            for num, name, definition in matches:
                concept_id = self._generate_concept_id(name)

                # Extract additional properties if present
                properties = {}
                examples = []

                # Look for properties in definition
                if "Properties:" in definition:
                    parts = definition.split("Properties:")
                    definition = parts[0].strip()
                    prop_text = parts[1].strip()

                    # Parse properties
                    properties = self._parse_properties(prop_text)

                # Look for examples
                if "Examples:" in definition:
                    parts = definition.split("Examples:")
                    definition = parts[0].strip()
                    example_text = parts[1].strip()
                    examples = [e.strip() for e in example_text.split(',')]

                concepts.append(Concept(
                    id=concept_id,
                    name=name.strip(),
                    definition=definition.strip(),
                    properties=properties,
                    examples=examples
                ))

        # If no numbered list, try bullet format
        if not concepts:
            bullet_pattern = r'[-•]\s*([^:]+):\s*([^\n]+(?:\n(?![-•])[^\n]+)*)'
            matches = re.findall(bullet_pattern, raw_concepts, re.MULTILINE)

            for name, definition in matches:
                concept_id = self._generate_concept_id(name)
                concepts.append(Concept(
                    id=concept_id,
                    name=name.strip(),
                    definition=definition.strip()
                ))

        # If still no concepts, try paragraph format
        if not concepts:
            paragraphs = raw_concepts.split('\n\n')
            for para in paragraphs:
                if ':' in para:
                    name, definition = para.split(':', 1)
                    if len(name) < 50:  # Reasonable name length
                        concept_id = self._generate_concept_id(name)
                        concepts.append(Concept(
                            id=concept_id,
                            name=name.strip(),
                            definition=definition.strip()
                        ))

        if not concepts and self.strict_parsing:
            raise ValueError("Failed to parse any concepts from raw text")

        return concepts

    def parse_prerequisites(self, raw_prereqs: str,
                          concept_index: Dict[str, str]) -> List[Relationship]:
        """
        Parse prerequisite relationships.

        Expected format: "Concept -> [Prereq1, Prereq2, ...]"
        """
        relationships = []

        # Pattern for "A -> [B, C, D]" format
        arrow_pattern = r'([^->]+)->\s*\[([^\]]*)\]'
        matches = re.findall(arrow_pattern, raw_prereqs)

        for target_name, prereq_list in matches:
            target_name = target_name.strip().lower()
            target_id = concept_index.get(target_name)

            if not target_id:
                target_id = self._fuzzy_match_concept(target_name, concept_index)

            if target_id and prereq_list.strip():
                # Parse prerequisite list
                prereqs = [p.strip() for p in prereq_list.split(',')]

                for prereq_name in prereqs:
                    prereq_name_lower = prereq_name.lower()
                    source_id = concept_index.get(prereq_name_lower)

                    if not source_id:
                        source_id = self._fuzzy_match_concept(
                            prereq_name_lower,
                            concept_index
                        )

                    if source_id:
                        relationships.append(Relationship(
                            source=source_id,
                            target=target_id,
                            type=RelationshipType.PREREQUISITE,
                            description=f"{prereq_name} is prerequisite for {target_name}"
                        ))

        return relationships

    def parse_causal_relationships(self, raw_causal: str,
                                  concept_index: Dict[str, str]) -> List[Relationship]:
        """
        Parse causal relationships.

        Expected format: "Cause -> Effect (explanation)"
        """
        relationships = []

        # Pattern for "A -> B (explanation)" format
        causal_pattern = r'([^->]+)->\s*([^(\n]+)(?:\(([^)]+)\))?'
        matches = re.findall(causal_pattern, raw_causal)

        for cause_name, effect_name, explanation in matches:
            cause_name = cause_name.strip().lower()
            effect_name = effect_name.strip().lower()

            cause_id = concept_index.get(cause_name)
            if not cause_id:
                cause_id = self._fuzzy_match_concept(cause_name, concept_index)

            effect_id = concept_index.get(effect_name)
            if not effect_id:
                effect_id = self._fuzzy_match_concept(effect_name, concept_index)

            if cause_id and effect_id:
                relationships.append(Relationship(
                    source=cause_id,
                    target=effect_id,
                    type=RelationshipType.CAUSAL,
                    description=explanation.strip() if explanation else None
                ))

        return relationships

    def parse_axioms(self, raw_axioms: str,
                    concept_index: Dict[str, str]) -> List[Axiom]:
        """
        Parse axioms and fundamental laws.

        Expected format:
        1. Statement
        2. Formal expression (optional)
        3. Concepts involved
        4. Derivable theorems
        """
        axioms = []
        axiom_counter = 0

        # Try to parse numbered axioms
        sections = re.split(r'\n\d+\.\s+', raw_axioms)

        for section in sections[1:]:  # Skip first empty section
            axiom_counter += 1
            axiom_id = f"axiom_{axiom_counter:03d}"

            lines = section.strip().split('\n')
            statement = lines[0] if lines else ""

            formal_expression = None
            concepts_involved = []
            derivable_theorems = []

            # Parse additional information
            current_section = None
            for line in lines[1:]:
                line_lower = line.lower()

                if 'formal' in line_lower or 'mathematical' in line_lower:
                    current_section = 'formal'
                elif 'concept' in line_lower and 'involved' in line_lower:
                    current_section = 'concepts'
                elif 'derivable' in line_lower or 'derive' in line_lower:
                    current_section = 'theorems'
                elif current_section == 'formal':
                    formal_expression = line.strip()
                elif current_section == 'concepts':
                    # Extract concept references
                    for concept_name in concept_index.keys():
                        if concept_name in line_lower:
                            concepts_involved.append(concept_index[concept_name])
                elif current_section == 'theorems':
                    derivable_theorems.append(line.strip())

            if statement:
                axioms.append(Axiom(
                    id=axiom_id,
                    statement=statement,
                    formal_expression=formal_expression,
                    concepts_involved=list(set(concepts_involved)),
                    derivable_theorems=derivable_theorems
                ))

        # If no numbered format, try paragraph format
        if not axioms:
            paragraphs = raw_axioms.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    axiom_counter += 1
                    axioms.append(Axiom(
                        id=f"axiom_{axiom_counter:03d}",
                        statement=para.strip()
                    ))

        return axioms

    def _generate_concept_id(self, name: str) -> str:
        """Generate a unique ID for a concept."""
        self.concept_counter += 1
        # Create ID from name and counter
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        return f"concept_{clean_name}_{self.concept_counter:03d}"

    def _parse_properties(self, prop_text: str) -> Dict[str, Any]:
        """Parse properties from text."""
        properties = {}

        # Try key-value format
        kv_pattern = r'(\w+):\s*([^,\n]+)'
        matches = re.findall(kv_pattern, prop_text)

        for key, value in matches:
            properties[key.strip()] = value.strip()

        # If no key-value pairs, store as single property
        if not properties and prop_text.strip():
            properties["description"] = prop_text.strip()

        return properties

    def _fuzzy_match_concept(self, name: str,
                            concept_index: Dict[str, str]) -> Optional[str]:
        """
        Attempt fuzzy matching for concept names.

        Returns concept ID if match found, None otherwise.
        """
        name_lower = name.lower()

        # Try partial matches
        for concept_name, concept_id in concept_index.items():
            # Check if one contains the other
            if name_lower in concept_name or concept_name in name_lower:
                return concept_id

            # Check word overlap
            name_words = set(name_lower.split())
            concept_words = set(concept_name.split())
            if len(name_words & concept_words) >= min(len(name_words), len(concept_words)) * 0.5:
                return concept_id

        return None

    def validate_model(self, model: StructuredModel) -> Dict[str, Any]:
        """
        Validate extracted model for consistency and completeness.

        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        errors = []
        stats = {}

        # Check for orphan concepts (no relationships)
        connected_concepts = set()
        for rel in model.relationships:
            connected_concepts.add(rel.source)
            connected_concepts.add(rel.target)

        all_concepts = {c.id for c in model.concepts}
        orphans = all_concepts - connected_concepts

        if orphans:
            warnings.append(f"Found {len(orphans)} orphan concepts with no relationships")

        # Check for circular prerequisites
        prereq_rels = [r for r in model.relationships
                      if r.type == RelationshipType.PREREQUISITE]
        cycles = self._find_cycles(prereq_rels)
        if cycles:
            errors.append(f"Found circular prerequisite dependencies: {cycles}")

        # Calculate statistics
        stats["num_concepts"] = len(model.concepts)
        stats["num_relationships"] = len(model.relationships)
        stats["num_axioms"] = len(model.axioms)
        stats["num_orphans"] = len(orphans)
        stats["avg_relationships_per_concept"] = (
            len(model.relationships) / len(model.concepts)
            if model.concepts else 0
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "statistics": stats
        }

    def _find_cycles(self, relationships: List[Relationship]) -> List[List[str]]:
        """Find cycles in directed relationships."""
        # Build adjacency list
        graph = {}
        for rel in relationships:
            if rel.source not in graph:
                graph[rel.source] = []
            graph[rel.source].append(rel.target)

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor, path[:]):
                            return True
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles