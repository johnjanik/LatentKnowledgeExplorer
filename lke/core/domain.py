"""
Domain configuration and management for the Latent Knowledge Explorer.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
import yaml
import json
from pathlib import Path


@dataclass
class PromptTemplate:
    """Template for generating prompts."""
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")
        return self.template.format(**kwargs)


@dataclass
class Benchmark:
    """Benchmark problem for evaluating extracted models."""
    name: str
    type: str  # 'prediction', 'classification', 'derivation', etc.
    description: str
    input: Dict[str, Any]
    expected_output: Any
    tolerance: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "input": self.input,
            "expected_output": self.expected_output,
            "tolerance": self.tolerance,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Benchmark":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DomainConfig:
    """Configuration for a scientific domain."""

    name: str
    version: str
    description: str

    # Prompt templates
    concept_prompt_template: Optional[PromptTemplate] = None
    prerequisite_prompt_template: Optional[PromptTemplate] = None
    causal_prompt_template: Optional[PromptTemplate] = None
    axiom_prompt_template: Optional[PromptTemplate] = None
    custom_templates: Dict[str, PromptTemplate] = field(default_factory=dict)

    # Benchmarks
    benchmarks: List[Benchmark] = field(default_factory=list)

    # Processing parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Focusing keywords for initial extraction
    focusing_keywords: List[str] = field(default_factory=list)

    # Structured context patterns
    context_patterns: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Set default templates if not provided."""
        if not self.concept_prompt_template:
            self.concept_prompt_template = PromptTemplate(
                name="concept_discovery",
                template=(
                    "You are an expert in {domain_description}.\n"
                    "List the fundamental concepts and quantities in this domain.\n"
                    "For each concept, provide:\n"
                    "1. Name\n"
                    "2. Brief definition (1-2 sentences)\n"
                    "3. Key properties or characteristics\n"
                    "4. Common examples if applicable\n\n"
                    "Format your response as a numbered list."
                ),
                variables=["domain_description"]
            )

        if not self.prerequisite_prompt_template:
            self.prerequisite_prompt_template = PromptTemplate(
                name="prerequisite_extraction",
                template=(
                    "Given the following list of concepts in {domain_description}:\n\n"
                    "{concept_list}\n\n"
                    "For each concept, identify which other concepts from the list are prerequisites "
                    "(must be understood first).\n"
                    "Format as: 'Concept -> [Prerequisite1, Prerequisite2, ...]'\n"
                    "If a concept has no prerequisites from the list, write: 'Concept -> []'"
                ),
                variables=["domain_description", "concept_list"]
            )

        if not self.causal_prompt_template:
            self.causal_prompt_template = PromptTemplate(
                name="causal_extraction",
                template=(
                    "Given the following concepts in {domain_description}:\n\n"
                    "{concept_list}\n\n"
                    "Identify the causal relationships between these concepts.\n"
                    "A causal relationship means that changes in one concept directly cause "
                    "changes in another.\n"
                    "Format as: 'Cause -> Effect (brief explanation)'\n"
                    "List all significant causal relationships."
                ),
                variables=["domain_description", "concept_list"]
            )

        if not self.axiom_prompt_template:
            self.axiom_prompt_template = PromptTemplate(
                name="axiom_extraction",
                template=(
                    "Given these concepts in {domain_description}:\n\n"
                    "{concept_list}\n\n"
                    "Propose a minimal set of axioms, fundamental laws, or principles "
                    "from which other relationships can be derived.\n"
                    "For each axiom:\n"
                    "1. State the axiom clearly\n"
                    "2. If possible, provide a mathematical or formal expression\n"
                    "3. List which concepts are involved\n"
                    "4. Briefly explain what can be derived from it"
                ),
                variables=["domain_description", "concept_list"]
            )

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        if name == "concept":
            return self.concept_prompt_template
        elif name == "prerequisite":
            return self.prerequisite_prompt_template
        elif name == "causal":
            return self.causal_prompt_template
        elif name == "axiom":
            return self.axiom_prompt_template
        else:
            return self.custom_templates.get(name)

    def add_template(self, name: str, template: PromptTemplate):
        """Add a custom prompt template."""
        self.custom_templates[name] = template

    def add_benchmark(self, benchmark: Benchmark):
        """Add a benchmark problem."""
        self.benchmarks.append(benchmark)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a configuration parameter."""
        return self.parameters.get(key, default)

    def set_parameter(self, key: str, value: Any):
        """Set a configuration parameter."""
        self.parameters[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "templates": {
                "concept": self._template_to_dict(self.concept_prompt_template),
                "prerequisite": self._template_to_dict(self.prerequisite_prompt_template),
                "causal": self._template_to_dict(self.causal_prompt_template),
                "axiom": self._template_to_dict(self.axiom_prompt_template),
                **{k: self._template_to_dict(v) for k, v in self.custom_templates.items()}
            },
            "benchmarks": [b.to_dict() for b in self.benchmarks],
            "parameters": self.parameters,
            "focusing_keywords": self.focusing_keywords,
            "context_patterns": self.context_patterns
        }

    def _template_to_dict(self, template: Optional[PromptTemplate]) -> Optional[Dict[str, Any]]:
        """Convert template to dictionary."""
        if not template:
            return None
        return {
            "name": template.name,
            "template": template.template,
            "variables": template.variables,
            "description": template.description
        }

    def save_to_file(self, filepath: str):
        """Save configuration to YAML file."""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> "DomainConfig":
        """Load configuration from YAML or JSON file."""
        filepath = Path(filepath)

        if filepath.suffix in ['.yaml', '.yml']:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        elif filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainConfig":
        """Create configuration from dictionary."""
        # Extract basic fields
        config = cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data["description"]
        )

        # Load templates
        templates = data.get("templates", {})
        if "concept" in templates:
            config.concept_prompt_template = cls._dict_to_template(templates["concept"])
        if "prerequisite" in templates:
            config.prerequisite_prompt_template = cls._dict_to_template(templates["prerequisite"])
        if "causal" in templates:
            config.causal_prompt_template = cls._dict_to_template(templates["causal"])
        if "axiom" in templates:
            config.axiom_prompt_template = cls._dict_to_template(templates["axiom"])

        # Load custom templates
        for key, template_data in templates.items():
            if key not in ["concept", "prerequisite", "causal", "axiom"]:
                config.custom_templates[key] = cls._dict_to_template(template_data)

        # Load benchmarks
        config.benchmarks = [
            Benchmark.from_dict(b) for b in data.get("benchmarks", [])
        ]

        # Load parameters
        config.parameters = data.get("parameters", {})
        config.focusing_keywords = data.get("focusing_keywords", [])
        config.context_patterns = data.get("context_patterns", {})

        return config

    @classmethod
    def _dict_to_template(cls, data: Dict[str, Any]) -> PromptTemplate:
        """Convert dictionary to PromptTemplate."""
        return PromptTemplate(
            name=data.get("name", ""),
            template=data["template"],
            variables=data.get("variables", []),
            description=data.get("description")
        )


class DomainManager:
    """Manager for multiple domain configurations."""

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize domain manager.

        Args:
            config_dir: Directory containing domain configuration files
        """
        self.config_dir = config_dir or os.path.expanduser("~/.lke/domains")
        os.makedirs(self.config_dir, exist_ok=True)
        self.domains: Dict[str, DomainConfig] = {}
        self._load_domains()

    def _load_domains(self):
        """Load all domain configurations from directory."""
        config_path = Path(self.config_dir)
        for file in config_path.glob("*.yaml"):
            try:
                domain = DomainConfig.load_from_file(file)
                self.domains[domain.name] = domain
            except Exception as e:
                print(f"Warning: Failed to load domain from {file}: {e}")

        for file in config_path.glob("*.yml"):
            try:
                domain = DomainConfig.load_from_file(file)
                self.domains[domain.name] = domain
            except Exception as e:
                print(f"Warning: Failed to load domain from {file}: {e}")

    def get_domain(self, name: str) -> Optional[DomainConfig]:
        """Get domain configuration by name."""
        return self.domains.get(name)

    def add_domain(self, domain: DomainConfig, save: bool = True):
        """Add or update a domain configuration."""
        self.domains[domain.name] = domain
        if save:
            filepath = os.path.join(self.config_dir, f"{domain.name}.yaml")
            domain.save_to_file(filepath)

    def remove_domain(self, name: str, delete_file: bool = True):
        """Remove a domain configuration."""
        if name in self.domains:
            if delete_file:
                filepath = os.path.join(self.config_dir, f"{name}.yaml")
                if os.path.exists(filepath):
                    os.remove(filepath)
            del self.domains[name]

    def list_domains(self) -> List[str]:
        """List available domain names."""
        return list(self.domains.keys())

    def reload(self):
        """Reload all domain configurations from disk."""
        self.domains.clear()
        self._load_domains()