# Latent Knowledge Explorer (LKE)

Extract structured scientific understanding from Large Language Models.

## Overview

The Latent Knowledge Explorer (LKE) is a Python application that systematically interrogates Large Language Models (LLMs) to extract structured knowledge representations. It implements the Latent-Space Structural Realism (LSSR) hypothesis, providing tools to build explicit models of scientific domains from implicit LLM knowledge.

## Features

- **Multi-Provider Support**: Works with Claude (API/CLI), OpenAI, and Ollama (local models)
- **Domain-Agnostic**: Configurable for any scientific field
- **Structured Extraction**: Builds knowledge graphs, causal models, and axiom systems
- **Iterative Refinement**: Uses reflection loops to improve extraction quality
- **Plugin Architecture**: Extensible with custom domain logic
- **Caching System**: Reduces API costs and speeds up repeated queries

## Installation

### Requirements

- Python 3.9 or higher
- macOS or Linux (Windows not supported)
- 8GB RAM minimum (16GB recommended)

### Quick Install (One-Liners)

#### Ubuntu/Debian (recommended for CLI tools):
```bash
pipx install git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
```

#### With UV (fastest, cross-platform):
```bash
uv pip install --system git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
```

#### macOS with Homebrew:
```bash
brew install --HEAD johnjanik/tap/lke
```

#### Traditional pip (requires virtual environment):
```bash
python3 -m pip install --user git+https://github.com/johnjanik/LatentKnowledgeExplorer.git
```

### Development Install

```bash
git clone https://github.com/johnjanik/LatentKnowledgeExplorer.git
cd LatentKnowledgeExplorer
uv pip install -e .  # or: python3 -m pip install -e .
```

### Provider-Specific Setup

#### For Claude API:
```bash
pip install anthropic
lke configure --provider claude-api --api-key YOUR_API_KEY
```

#### For Ollama (Local Models):
```bash
# Install Ollama first: https://ollama.ai
ollama pull llama2  # or any model you prefer
lke configure --provider ollama --model llama2
```

#### For OpenAI:
```bash
pip install openai
lke configure --provider openai --api-key YOUR_API_KEY
```

## Quick Start

### 1. Configure LKE

```bash
lke configure
```

This will prompt you for:
- LLM provider selection
- API credentials (if needed)
- Model preferences

### 2. Initialize a Domain

```bash
lke init-domain biology --description "Molecular biology and genetics"
```

### 3. Extract Knowledge

```bash
lke extract biology --output-dir ./results
```

### 4. View Results

The extraction creates structured JSON/YAML files containing:
- Concepts with definitions
- Prerequisite relationships
- Causal connections
- Fundamental axioms

## Usage Examples

### Command Line Interface

```bash
# List available domains
lke list-domains

# Extract knowledge with custom input
lke extract physics --input data.json --iterations 3

# Start interactive session
lke interactive chemistry

# Check Ollama models
lke check-ollama
```

### Python API

```python
from lke import DomainConfig, InterrogationEngine, create_llm_interface

# Create LLM interface
llm = create_llm_interface("ollama", model="llama2")

# Define domain
domain = DomainConfig(
    name="neuroscience",
    description="Study of the nervous system",
    version="1.0.0"
)

# Extract knowledge
engine = InterrogationEngine(llm, domain)
result = engine.extract_knowledge()

# Process results
print(f"Extracted {len(result.concepts)} concepts")
```

## Domain Configuration

Domains are configured using YAML files:

```yaml
domain:
  name: "quantum_mechanics"
  version: "1.0.0"
  description: "Quantum mechanical systems and phenomena"

parameters:
  max_concepts: 50
  extraction_iterations: 3
  confidence_threshold: 0.8

focusing_keywords:
  - "quantum state"
  - "superposition"
  - "entanglement"
  - "measurement"

context_patterns:
  mathematical_structure: "Identify key mathematical formalisms"
  experimental_basis: "Note experimental validations"
```

## Architecture

The system implements a pipeline based on the provided block diagram:

1. **Input Processing**: Data to judge/analyze
2. **Focusing Keywords**: Domain-specific term extraction
3. **Structured Context**: Apply domain knowledge patterns
4. **Semantic Enrichment**: Find related concepts
5. **Relevance Ranking**: Prioritize important information
6. **Chain-of-Thought**: Generate reasoning chains
7. **Reflection Loop**: Iterative refinement
8. **Domain Logic**: User-implemented scientific reasoning

## Plugin Development

Create custom domain logic by extending the base plugin:

```python
from lke.plugins import DomainLogicPlugin

class PhysicsLogic(DomainLogicPlugin):
    def validate_concepts(self, concepts):
        # Apply physics-specific validation
        return validated_concepts

    def compute_relationships(self, concepts):
        # Derive physical relationships
        return relationships
```

## Output Format

Extracted models are saved as structured JSON/YAML:

```json
{
  "domain_name": "biology",
  "concepts": [
    {
      "id": "gene_001",
      "name": "gene",
      "definition": "A sequence of nucleotides...",
      "properties": {...}
    }
  ],
  "relationships": [
    {
      "source": "gene_001",
      "target": "protein_001",
      "type": "causal",
      "description": "Transcription and translation"
    }
  ],
  "axioms": [
    {
      "statement": "Central dogma: DNA -> RNA -> Protein",
      "formal_expression": "..."
    }
  ]
}
```

## Troubleshooting

### Ollama Connection Issues

If Ollama isn't connecting:
1. Ensure Ollama is running: `ollama serve`
2. Check the host URL: default is `http://localhost:11434`
3. Verify model is installed: `ollama list`

### API Rate Limits

The system includes automatic caching to reduce API calls. Configure cache directory:
```bash
lke configure --cache-dir ~/.lke/cache
```

### Memory Issues

For large domains, reduce extraction scope:
```yaml
parameters:
  max_concepts: 20
  extraction_iterations: 1
```

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Citation

If you use LKE in research, please cite:
```bibtex
@software{lke2024,
  title = {Latent Knowledge Explorer},
  author = {LKE Team},
  year = {2024},
  url = {https://github.com/johnjanik/LatentKnowledgeExplorer}
}
```

## Support

- Issues: [GitHub Issues](https://github.com/johnjanik/LatentKnowledgeExplorer/issues)
- Documentation: [Full Docs](https://github.com/johnjanik/LatentKnowledgeExplorer/wiki)