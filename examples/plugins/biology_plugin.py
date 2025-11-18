"""
Example biology domain logic plugin.

This demonstrates how scientists can implement domain-specific reasoning.
"""

from typing import Dict, List, Any
import re

from lke.plugins.base import DomainLogicPlugin


class BiologyDomainLogic(DomainLogicPlugin):
    """
    Biology-specific logic for molecular biology and genetics.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with biology-specific resources."""
        super().__init__(config)

        # Define biological hierarchies
        self.molecular_hierarchy = [
            "atom", "molecule", "macromolecule", "complex",
            "organelle", "cell", "tissue", "organ", "system", "organism"
        ]

        # Central dogma relationships
        self.central_dogma = {
            "DNA": ["RNA"],
            "RNA": ["Protein"],
            "Gene": ["mRNA", "Transcription"],
            "mRNA": ["Protein", "Translation"]
        }

        # Common biological patterns
        self.pathway_patterns = [
            r"(\w+)\s+phosphorylates\s+(\w+)",
            r"(\w+)\s+activates\s+(\w+)",
            r"(\w+)\s+inhibits\s+(\w+)",
            r"(\w+)\s+binds\s+to\s+(\w+)",
            r"(\w+)\s+cleaves\s+(\w+)"
        ]

    def preprocess_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize biological nomenclature.

        Args:
            data: Raw input data

        Returns:
            Preprocessed data with standardized terms
        """
        processed = data.copy()

        # Standardize gene names (uppercase for human genes)
        if "genes" in processed:
            processed["genes"] = [g.upper() for g in processed["genes"]]

        # Standardize protein names
        if "proteins" in processed:
            processed["proteins"] = self._standardize_protein_names(processed["proteins"])

        # Add biological context
        if "experiment_type" in processed:
            processed["biological_context"] = self._get_experimental_context(
                processed["experiment_type"]
            )

        return processed

    def validate_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """
        Validate biological concepts for accuracy.

        Args:
            concepts: List of extracted concepts

        Returns:
            Validated concepts with corrections
        """
        validated = []

        for concept in concepts:
            name = concept.get("name", "").lower()
            definition = concept.get("definition", "")

            # Check for common misconceptions
            if "gene" in name and "protein" in definition:
                concept["warning"] = "Genes encode proteins but are not proteins themselves"

            # Validate molecular biology terms
            if name in ["dna", "rna", "mrna", "trna", "rrna"]:
                concept["category"] = "nucleic_acid"
                concept["validated"] = True

            # Check protein-related concepts
            if "enzyme" in name or name.endswith("ase"):
                concept["category"] = "protein"
                concept["function"] = "catalytic"

            # Validate cellular components
            if name in ["nucleus", "mitochondria", "ribosome", "endoplasmic reticulum"]:
                concept["category"] = "organelle"
                concept["validated"] = True

            # Add hierarchical level
            concept["hierarchy_level"] = self._get_hierarchy_level(name)

            validated.append(concept)

        return validated

    def compute_relationships(self, concepts: List[Dict]) -> Dict[str, List[str]]:
        """
        Derive biological relationships from concepts.

        Args:
            concepts: List of validated concepts

        Returns:
            Relationships based on biological knowledge
        """
        relationships = {}
        concept_map = {c["name"].lower(): c.get("id", c["name"]) for c in concepts}

        for concept in concepts:
            name = concept.get("name", "").lower()
            concept_id = concept.get("id", name)
            relationships[concept_id] = []

            # Apply central dogma relationships
            if name in self.central_dogma:
                for target in self.central_dogma[name]:
                    target_lower = target.lower()
                    if target_lower in concept_map:
                        relationships[concept_id].append(concept_map[target_lower])

            # Check for enzyme-substrate relationships
            if concept.get("function") == "catalytic":
                # Look for substrate in definition
                definition = concept.get("definition", "")
                for other_concept in concepts:
                    other_name = other_concept.get("name", "")
                    if other_name in definition and "substrate" in definition:
                        relationships[concept_id].append(
                            other_concept.get("id", other_name)
                        )

            # Add hierarchical relationships
            level = concept.get("hierarchy_level")
            if level and level > 0:
                # Find concepts at the next lower level
                for other in concepts:
                    other_level = other.get("hierarchy_level")
                    if other_level == level - 1:
                        # Check if mentioned in definition
                        if other["name"] in concept.get("definition", ""):
                            relationships[concept_id].append(
                                other.get("id", other["name"])
                            )

        return relationships

    def evaluate_consistency(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check biological consistency of the model.

        Args:
            model: Complete extracted model

        Returns:
            Validation results with biological constraints checked
        """
        errors = []
        warnings = []
        suggestions = []

        concepts = model.get("concepts", [])
        relationships = model.get("relationships", [])

        # Check central dogma consistency
        has_dna = any(c.get("name", "").lower() == "dna" for c in concepts)
        has_rna = any(c.get("name", "").lower() in ["rna", "mrna"] for c in concepts)
        has_protein = any(c.get("name", "").lower() == "protein" for c in concepts)

        if has_dna and has_protein and not has_rna:
            warnings.append("Missing RNA in central dogma pathway")
            suggestions.append("Add RNA/mRNA concept to complete information flow")

        # Check for orphan metabolites
        metabolites = [c for c in concepts if c.get("category") == "metabolite"]
        for metabolite in metabolites:
            met_id = metabolite.get("id")
            has_relationship = any(
                r.get("source") == met_id or r.get("target") == met_id
                for r in relationships
            )
            if not has_relationship:
                warnings.append(f"Metabolite {metabolite.get('name')} has no pathway connections")

        # Validate enzyme-substrate pairs
        enzymes = [c for c in concepts if c.get("function") == "catalytic"]
        for enzyme in enzymes:
            enzyme_id = enzyme.get("id")
            has_substrate = any(
                r.get("source") == enzyme_id and "substrate" in r.get("description", "")
                for r in relationships
            )
            if not has_substrate:
                warnings.append(f"Enzyme {enzyme.get('name')} missing substrate relationship")

        # Check for circular dependencies in regulatory networks
        regulatory_rels = [
            r for r in relationships
            if "regulate" in r.get("description", "").lower()
        ]
        cycles = self._find_regulatory_cycles(regulatory_rels)
        if cycles:
            warnings.append(f"Found {len(cycles)} potential feedback loops")
            suggestions.append("Verify feedback loops are biologically accurate")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "statistics": {
                "num_enzymes": len(enzymes),
                "num_metabolites": len(metabolites),
                "central_dogma_complete": has_dna and has_rna and has_protein
            }
        }

    def enrich_with_knowledge(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add biological annotations and known pathways.

        Args:
            model: Extracted model

        Returns:
            Enriched model with biological annotations
        """
        enriched = model.copy()

        # Add KEGG pathway annotations if available
        concepts = enriched.get("concepts", [])
        for concept in concepts:
            name = concept.get("name", "").upper()

            # Add gene ontology categories
            if concept.get("category") == "protein":
                concept["go_categories"] = self._get_go_categories(name)

            # Add known drug targets
            if concept.get("function") == "catalytic":
                concept["drug_target"] = self._is_drug_target(name)

        # Add pathway groupings
        enriched["pathways"] = self._group_into_pathways(concepts, model.get("relationships", []))

        return enriched

    def suggest_experiments(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest biological experiments to validate the model.

        Args:
            model: Extracted model

        Returns:
            List of suggested experiments
        """
        experiments = []
        concepts = model.get("concepts", [])

        # Suggest knockout experiments for genes
        genes = [c for c in concepts if "gene" in c.get("name", "").lower()]
        for gene in genes[:3]:  # Limit to top 3
            experiments.append({
                "type": "knockout",
                "target": gene.get("name"),
                "description": f"CRISPR knockout of {gene.get('name')} to validate function",
                "expected_outcome": "Loss of downstream pathway activity"
            })

        # Suggest protein interaction studies
        proteins = [c for c in concepts if c.get("category") == "protein"]
        if len(proteins) >= 2:
            experiments.append({
                "type": "co-immunoprecipitation",
                "targets": [p.get("name") for p in proteins[:2]],
                "description": "Test for direct protein-protein interaction",
                "expected_outcome": "Confirm or refute predicted interaction"
            })

        # Suggest metabolomics for pathways
        if model.get("pathways"):
            experiments.append({
                "type": "metabolomics",
                "description": "Mass spectrometry analysis of metabolite levels",
                "expected_outcome": "Validate predicted metabolic relationships"
            })

        return experiments

    # Helper methods
    def _standardize_protein_names(self, proteins: List[str]) -> List[str]:
        """Standardize protein nomenclature."""
        standardized = []
        for protein in proteins:
            # Remove species prefixes
            name = re.sub(r'^[hm]', '', protein, flags=re.IGNORECASE)
            # Uppercase human proteins
            standardized.append(name.upper())
        return standardized

    def _get_experimental_context(self, experiment_type: str) -> str:
        """Get biological context for experiment type."""
        contexts = {
            "in_vitro": "Cell-free system",
            "cell_culture": "Cultured cells",
            "in_vivo": "Living organism",
            "clinical": "Human subjects"
        }
        return contexts.get(experiment_type, "Unknown context")

    def _get_hierarchy_level(self, name: str) -> int:
        """Get biological hierarchy level."""
        name_lower = name.lower()
        for i, level in enumerate(self.molecular_hierarchy):
            if level in name_lower:
                return i
        return -1

    def _find_regulatory_cycles(self, relationships: List[Dict]) -> List[List[str]]:
        """Find cycles in regulatory networks."""
        # Simplified cycle detection
        cycles = []
        # Implementation would use graph algorithms
        return cycles

    def _get_go_categories(self, protein_name: str) -> List[str]:
        """Get Gene Ontology categories (mock implementation)."""
        # In real implementation, would query GO database
        return ["molecular_function", "biological_process"]

    def _is_drug_target(self, enzyme_name: str) -> bool:
        """Check if enzyme is a known drug target (mock)."""
        # In real implementation, would query drug databases
        known_targets = ["kinase", "protease", "polymerase"]
        return any(target in enzyme_name.lower() for target in known_targets)

    def _group_into_pathways(self, concepts: List[Dict], relationships: List[Dict]) -> List[Dict]:
        """Group concepts into biological pathways."""
        # Simplified pathway grouping
        pathways = []

        # Check for glycolysis components
        glycolysis_terms = ["glucose", "pyruvate", "atp", "glycolysis"]
        glycolysis_concepts = [
            c for c in concepts
            if any(term in c.get("name", "").lower() for term in glycolysis_terms)
        ]
        if len(glycolysis_concepts) >= 2:
            pathways.append({
                "name": "Glycolysis",
                "concepts": [c.get("id") for c in glycolysis_concepts],
                "type": "metabolic"
            })

        return pathways