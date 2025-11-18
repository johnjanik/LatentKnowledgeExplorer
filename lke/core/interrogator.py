"""
Interrogation engine for extracting structured knowledge from LLMs.
"""

from typing import Dict, Any, Optional, List, Tuple
import time
import json
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from ..interfaces.llm_interface import LLMInterface, LLMResponse
from ..core.domain import DomainConfig


@dataclass
class InterrogationResult:
    """Result of an interrogation session."""
    raw_concepts: str
    raw_prerequisites: str
    raw_causal: str
    raw_axioms: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    iterations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "raw_concepts": self.raw_concepts,
            "raw_prerequisites": self.raw_prerequisites,
            "raw_causal": self.raw_causal,
            "raw_axioms": self.raw_axioms,
            "metadata": self.metadata,
            "iterations": self.iterations
        }


class InterrogationEngine:
    """
    Engine for systematically interrogating LLMs to extract domain knowledge.

    Implements the pipeline from the block diagram:
    1. Focusing keywords
    2. Structured context building
    3. Semantic similarity enrichment
    4. Text relevance ranking
    5. Chain-of-thought effect prediction
    6. Over-sampling with reflection
    """

    def __init__(self, llm: LLMInterface, domain: DomainConfig,
                 enable_reflection: bool = True,
                 max_iterations: int = 3,
                 parallel_queries: int = 4):
        """
        Initialize interrogation engine.

        Args:
            llm: LLM interface to use
            domain: Domain configuration
            enable_reflection: Enable iterative refinement with reflection
            max_iterations: Maximum iterations for reflection loop
            parallel_queries: Number of parallel queries to execute
        """
        self.llm = llm
        self.domain = domain
        self.enable_reflection = enable_reflection
        self.max_iterations = max_iterations
        self.parallel_queries = parallel_queries
        self.query_cache = {}

    def extract_knowledge(self, input_data: Optional[Dict[str, Any]] = None) -> InterrogationResult:
        """
        Execute full knowledge extraction pipeline.

        Args:
            input_data: Optional input data to judge/analyze

        Returns:
            InterrogationResult containing all extracted knowledge
        """
        # Phase 1: Apply focusing keywords
        focused_context = self._apply_focusing_keywords(input_data)

        # Phase 2: Build structured context
        structured_context = self._build_structured_context(focused_context)

        # Phase 3: Initial extraction
        raw_concepts = self._extract_concepts(structured_context)

        # Phase 4: Iterative refinement with reflection
        if self.enable_reflection:
            raw_concepts = self._refine_with_reflection(
                raw_concepts,
                structured_context,
                "concepts"
            )

        # Phase 5: Extract relationships based on concepts
        raw_prerequisites = self._extract_prerequisites(raw_concepts)
        raw_causal = self._extract_causal_relationships(raw_concepts)
        raw_axioms = self._extract_axioms(raw_concepts)

        # Phase 6: Apply semantic enrichment and ranking
        if self.enable_reflection:
            raw_prerequisites = self._refine_with_reflection(
                raw_prerequisites,
                raw_concepts,
                "prerequisites"
            )
            raw_causal = self._refine_with_reflection(
                raw_causal,
                raw_concepts,
                "causal"
            )
            raw_axioms = self._refine_with_reflection(
                raw_axioms,
                raw_concepts,
                "axioms"
            )

        return InterrogationResult(
            raw_concepts=raw_concepts,
            raw_prerequisites=raw_prerequisites,
            raw_causal=raw_causal,
            raw_axioms=raw_axioms,
            metadata={
                "domain": self.domain.name,
                "timestamp": time.time(),
                "iterations": self.max_iterations if self.enable_reflection else 1
            }
        )

    def _apply_focusing_keywords(self, input_data: Optional[Dict[str, Any]]) -> str:
        """
        Apply focusing keywords to filter and contextualize input.

        This implements the "Focusing keywords" block from the diagram.
        """
        if not input_data:
            # Use domain description if no specific input
            context = self.domain.description
        else:
            # Extract relevant information using focusing keywords
            context_parts = [self.domain.description]

            # Add input data context
            if "hypothesis" in input_data:
                context_parts.append(f"Hypothesis: {input_data['hypothesis']}")
            if "data" in input_data:
                context_parts.append(f"Data: {json.dumps(input_data['data'])}")

            context = "\n".join(context_parts)

        # Apply focusing keywords if specified
        if self.domain.focusing_keywords:
            keyword_prompt = (
                f"Given the following context:\n{context}\n\n"
                f"Focus on these key aspects: {', '.join(self.domain.focusing_keywords)}\n"
                f"Provide a focused summary relevant to {self.domain.name}:"
            )

            response = self._query_llm(keyword_prompt)
            return response.text

        return context

    def _build_structured_context(self, focused_context: str) -> str:
        """
        Build structured context using domain patterns.

        This implements the "Structured biologic context" block (generalized to any domain).
        """
        if not self.domain.context_patterns:
            return focused_context

        # Apply structural patterns
        structured_parts = [focused_context]

        for pattern_name, pattern in self.domain.context_patterns.items():
            prompt = (
                f"Given this context:\n{focused_context}\n\n"
                f"Apply the following structural pattern ({pattern_name}):\n"
                f"{pattern}\n"
                f"Provide a structured analysis:"
            )

            response = self._query_llm(prompt)
            structured_parts.append(f"[{pattern_name}]\n{response.text}")

        return "\n\n".join(structured_parts)

    def _extract_concepts(self, context: str) -> str:
        """Extract fundamental concepts from the domain."""
        template = self.domain.concept_prompt_template
        prompt = template.format(
            domain_description=f"{self.domain.description}\n\nContext:\n{context}"
        )
        response = self._query_llm(prompt)
        return response.text

    def _extract_prerequisites(self, concepts: str) -> str:
        """Extract prerequisite relationships between concepts."""
        template = self.domain.prerequisite_prompt_template
        prompt = template.format(
            domain_description=self.domain.description,
            concept_list=concepts
        )
        response = self._query_llm(prompt)
        return response.text

    def _extract_causal_relationships(self, concepts: str) -> str:
        """Extract causal relationships between concepts."""
        template = self.domain.causal_prompt_template
        prompt = template.format(
            domain_description=self.domain.description,
            concept_list=concepts
        )
        response = self._query_llm(prompt)
        return response.text

    def _extract_axioms(self, concepts: str) -> str:
        """Extract fundamental axioms and laws."""
        template = self.domain.axiom_prompt_template
        prompt = template.format(
            domain_description=self.domain.description,
            concept_list=concepts
        )
        response = self._query_llm(prompt)
        return response.text

    def _refine_with_reflection(self, initial_result: str, context: str,
                                result_type: str) -> str:
        """
        Refine results through iterative reflection.

        This implements "Over-sampling with reflection" from the diagram.
        """
        current_result = initial_result

        for iteration in range(self.max_iterations - 1):
            # Generate reflection prompt
            reflection_prompt = self._create_reflection_prompt(
                current_result, context, result_type
            )

            # Query for improvements
            response = self._query_llm(reflection_prompt)

            # Check if significant improvements were made
            if self._is_converged(current_result, response.text):
                break

            current_result = response.text

        return current_result

    def _create_reflection_prompt(self, current_result: str, context: str,
                                  result_type: str) -> str:
        """Create a reflection prompt for iterative improvement."""
        prompts = {
            "concepts": (
                f"Review these extracted concepts:\n{current_result}\n\n"
                f"Context:\n{context}\n\n"
                f"Please:\n"
                f"1. Check for missing important concepts\n"
                f"2. Verify definitions are accurate\n"
                f"3. Add any necessary clarifications\n"
                f"4. Remove any redundant or incorrect items\n"
                f"Provide an improved version:"
            ),
            "prerequisites": (
                f"Review these prerequisite relationships:\n{current_result}\n\n"
                f"Concepts:\n{context}\n\n"
                f"Please:\n"
                f"1. Verify all relationships are correct\n"
                f"2. Add any missing prerequisite connections\n"
                f"3. Remove incorrect relationships\n"
                f"4. Ensure logical consistency\n"
                f"Provide an improved version:"
            ),
            "causal": (
                f"Review these causal relationships:\n{current_result}\n\n"
                f"Concepts:\n{context}\n\n"
                f"Please:\n"
                f"1. Verify causality is correctly identified\n"
                f"2. Add missing causal connections\n"
                f"3. Remove spurious relationships\n"
                f"4. Clarify mechanism of causation where needed\n"
                f"Provide an improved version:"
            ),
            "axioms": (
                f"Review these axioms:\n{current_result}\n\n"
                f"Concepts:\n{context}\n\n"
                f"Please:\n"
                f"1. Verify axioms are truly fundamental\n"
                f"2. Check for redundancy (axioms derivable from others)\n"
                f"3. Ensure completeness for the domain\n"
                f"4. Improve formal expressions if applicable\n"
                f"Provide an improved version:"
            )
        }

        return prompts.get(result_type, prompts["concepts"])

    def _is_converged(self, old_result: str, new_result: str,
                      threshold: float = 0.9) -> bool:
        """
        Check if results have converged (minimal changes).

        Simple implementation using text similarity.
        """
        # Simple character-based similarity
        if len(old_result) == 0:
            return False

        # Check if results are very similar
        common = sum(1 for a, b in zip(old_result, new_result) if a == b)
        similarity = common / max(len(old_result), len(new_result))

        return similarity > threshold

    def _query_llm(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Query the LLM with caching.

        Implements semantic similarity enrichment through caching.
        """
        # Check cache
        cache_key = hashlib.sha256(f"{prompt}{json.dumps(kwargs)}".encode()).hexdigest()
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        # Query LLM
        response = self.llm.generate(prompt, **kwargs)

        # Cache result
        self.query_cache[cache_key] = response

        return response

    def parallel_extract(self, domains: List[DomainConfig]) -> Dict[str, InterrogationResult]:
        """
        Extract knowledge from multiple domains in parallel.

        Args:
            domains: List of domain configurations

        Returns:
            Dictionary mapping domain names to results
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.parallel_queries) as executor:
            # Submit extraction tasks
            future_to_domain = {
                executor.submit(self._extract_for_domain, domain): domain
                for domain in domains
            }

            # Collect results
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    results[domain.name] = result
                except Exception as e:
                    print(f"Error extracting from {domain.name}: {e}")
                    results[domain.name] = None

        return results

    def _extract_for_domain(self, domain: DomainConfig) -> InterrogationResult:
        """Extract knowledge for a specific domain."""
        # Save current domain
        original_domain = self.domain

        # Switch to new domain
        self.domain = domain

        # Extract knowledge
        result = self.extract_knowledge()

        # Restore original domain
        self.domain = original_domain

        return result

    def chain_of_thought_analysis(self, problem: str, concepts: str) -> str:
        """
        Apply chain-of-thought reasoning to analyze a problem.

        This implements "Chain-of-thought effect prediction" from the diagram.
        """
        cot_prompt = (
            f"Given these domain concepts:\n{concepts}\n\n"
            f"Problem to analyze:\n{problem}\n\n"
            f"Let's think step by step:\n"
            f"1. Identify relevant concepts from the list\n"
            f"2. Trace causal chains\n"
            f"3. Apply domain principles\n"
            f"4. Predict outcomes\n\n"
            f"Provide a detailed chain-of-thought analysis:"
        )

        response = self._query_llm(cot_prompt)
        return response.text

    def relevance_ranking(self, items: List[str], query: str) -> List[Tuple[str, float]]:
        """
        Rank items by relevance to a query.

        This implements "Text relevance ranking" from the diagram.
        """
        ranking_prompt = (
            f"Query: {query}\n\n"
            f"Rank these items by relevance (most relevant first):\n"
        )

        for i, item in enumerate(items, 1):
            ranking_prompt += f"{i}. {item}\n"

        ranking_prompt += (
            "\nProvide rankings as: 'Rank Position: Item Number (relevance score 0-1)'\n"
            "Example: '1: Item 3 (0.95)'"
        )

        response = self._query_llm(ranking_prompt)

        # Parse rankings (simplified parsing)
        ranked_items = []
        lines = response.text.strip().split('\n')

        for line in lines:
            try:
                # Extract item number and score
                if ':' in line and '(' in line:
                    parts = line.split(':')
                    item_part = parts[1].split('(')
                    item_num = int(''.join(filter(str.isdigit, item_part[0])))
                    score = float(item_part[1].rstrip(')'))

                    if 1 <= item_num <= len(items):
                        ranked_items.append((items[item_num - 1], score))
            except (ValueError, IndexError):
                continue

        return ranked_items