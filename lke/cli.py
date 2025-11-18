#!/usr/bin/env python3
"""
Command-line interface for the Latent Knowledge Explorer.
"""

import click
import os
import json
import yaml
from pathlib import Path
from typing import Optional
import sys

from .interfaces.llm_interface import create_llm_interface
from .core.domain import DomainConfig, DomainManager
from .core.interrogator import InterrogationEngine
from .extractors.structure_extractor import StructureExtractor
from .core.models import StructuredModel


# Configuration directory
CONFIG_DIR = Path.home() / ".lke"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Latent Knowledge Explorer - Extract structured knowledge from LLMs."""
    pass


@cli.command()
@click.option('--provider', type=click.Choice(['claude-api', 'claude-cli', 'openai', 'ollama']),
              prompt='Select LLM provider', help='LLM provider to use')
@click.option('--api-key', help='API key for the selected provider')
@click.option('--model', help='Model name (e.g., claude-3-opus, gpt-4, llama2)')
@click.option('--ollama-host', default='http://localhost:11434',
              help='Ollama host URL (for ollama provider)')
@click.option('--cache-dir', default=str(CONFIG_DIR / "cache"),
              help='Directory for caching LLM responses')
def configure(provider, api_key, model, ollama_host, cache_dir):
    """Configure LKE with API credentials and settings."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f) or {}

    # Update configuration
    config['provider'] = provider
    config['cache_dir'] = cache_dir

    if provider in ['claude-api', 'openai']:
        if not api_key:
            api_key = click.prompt('Enter API key', hide_input=True)
        config['api_key'] = api_key

    if provider == 'ollama':
        config['ollama_host'] = ollama_host

    if model:
        config['model'] = model
    else:
        # Default models
        default_models = {
            'claude-api': 'claude-3-opus-20240229',
            'claude-cli': 'claude-3-opus-20240229',
            'openai': 'gpt-4',
            'ollama': 'llama2'
        }
        config['model'] = default_models.get(provider, 'default')

    # Save configuration
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

    click.echo(f"Configuration saved to {CONFIG_FILE}")

    # Test connection
    click.echo("Testing connection...")
    try:
        llm = create_llm_interface(provider, **_get_llm_config(config))
        if llm.validate_connection():
            click.echo("✓ Connection successful!")
        else:
            click.echo("✗ Connection failed. Please check your settings.")
    except Exception as e:
        click.echo(f"✗ Error: {e}")


@cli.command()
@click.argument('domain_name')
@click.option('--description', prompt='Domain description',
              help='Description of the domain')
@click.option('--template', type=click.Choice(['standard', 'minimal', 'detailed']),
              default='standard', help='Template preset to use')
@click.option('--output', help='Output file for domain configuration')
def init_domain(domain_name, description, template, output):
    """Initialize a new domain configuration."""
    # Create domain configuration
    domain = DomainConfig(
        name=domain_name,
        version="1.0.0",
        description=description
    )

    # Add template-specific settings
    if template == 'detailed':
        # Add more detailed prompts and parameters
        domain.parameters['max_concepts'] = 100
        domain.parameters['extraction_iterations'] = 3
        domain.parameters['confidence_threshold'] = 0.8
    elif template == 'minimal':
        domain.parameters['max_concepts'] = 20
        domain.parameters['extraction_iterations'] = 1

    # Save domain configuration
    if not output:
        output = CONFIG_DIR / "domains" / f"{domain_name}.yaml"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    domain.save_to_file(str(output_path))
    click.echo(f"Domain configuration created: {output_path}")


@cli.command()
@click.argument('domain_name')
@click.option('--input', 'input_file', type=click.Path(exists=True),
              help='Input data file (JSON)')
@click.option('--output-dir', default='./results',
              help='Output directory for results')
@click.option('--iterations', default=2, help='Number of reflection iterations')
@click.option('--format', 'output_format',
              type=click.Choice(['json', 'yaml', 'all']),
              default='json', help='Output format')
def extract(domain_name, input_file, output_dir, iterations, output_format):
    """Extract structured knowledge for a domain."""
    # Load configuration
    config = _load_config()
    if not config:
        click.echo("Please run 'lke configure' first")
        return

    # Load domain
    domain_mgr = DomainManager(str(CONFIG_DIR / "domains"))
    domain = domain_mgr.get_domain(domain_name)

    if not domain:
        click.echo(f"Domain '{domain_name}' not found. Available domains:")
        for name in domain_mgr.list_domains():
            click.echo(f"  - {name}")
        return

    # Load input data if provided
    input_data = None
    if input_file:
        with open(input_file, 'r') as f:
            input_data = json.load(f)

    # Create LLM interface
    click.echo(f"Initializing {config['provider']} interface...")
    llm = create_llm_interface(config['provider'], **_get_llm_config(config))

    # Create interrogation engine
    click.echo("Starting knowledge extraction...")
    engine = InterrogationEngine(
        llm=llm,
        domain=domain,
        enable_reflection=iterations > 1,
        max_iterations=iterations
    )

    # Extract knowledge
    with click.progressbar(length=4, label='Extracting knowledge') as bar:
        bar.update(1, 'Extracting concepts')
        result = engine.extract_knowledge(input_data)

        bar.update(1, 'Parsing structure')
        extractor = StructureExtractor()
        model = extractor.extract_model(
            result,
            domain.name,
            domain.description
        )

        bar.update(1, 'Validating model')
        validation = extractor.validate_model(model)

        bar.update(1, 'Saving results')

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save results
    timestamp = model.extraction_date.strftime("%Y%m%d_%H%M%S")
    base_name = f"{domain_name}_{timestamp}"

    if output_format in ['json', 'all']:
        json_file = output_path / f"{base_name}.json"
        with open(json_file, 'w') as f:
            json.dump(model.to_dict(), f, indent=2, default=str)
        click.echo(f"Model saved to: {json_file}")

    if output_format in ['yaml', 'all']:
        yaml_file = output_path / f"{base_name}.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(model.to_dict(), f, default_flow_style=False, default=str)
        click.echo(f"Model saved to: {yaml_file}")

    # Save validation report
    validation_file = output_path / f"{base_name}_validation.json"
    with open(validation_file, 'w') as f:
        json.dump(validation, f, indent=2)
    click.echo(f"Validation report: {validation_file}")

    # Display summary
    click.echo("\n=== Extraction Summary ===")
    click.echo(f"Concepts extracted: {len(model.concepts)}")
    click.echo(f"Relationships found: {len(model.relationships)}")
    click.echo(f"Axioms identified: {len(model.axioms)}")

    if validation['warnings']:
        click.echo("\nWarnings:")
        for warning in validation['warnings']:
            click.echo(f"  ⚠ {warning}")

    if validation['errors']:
        click.echo("\nErrors:")
        for error in validation['errors']:
            click.echo(f"  ✗ {error}")


@cli.command()
@click.argument('model_file', type=click.Path(exists=True))
@click.option('--domain', help='Domain name for benchmarks')
@click.option('--benchmarks', type=click.Path(exists=True),
              help='Custom benchmarks file')
def evaluate(model_file, domain, benchmarks):
    """Evaluate an extracted model against benchmarks."""
    # Load model
    with open(model_file, 'r') as f:
        if model_file.endswith('.json'):
            data = json.load(f)
        else:
            data = yaml.safe_load(f)

    model = StructuredModel.from_dict(data)

    # Load benchmarks
    benchmark_list = []
    if benchmarks:
        with open(benchmarks, 'r') as f:
            benchmark_data = json.load(f) if benchmarks.endswith('.json') else yaml.safe_load(f)
            # Parse benchmarks
    elif domain:
        domain_mgr = DomainManager(str(CONFIG_DIR / "domains"))
        domain_config = domain_mgr.get_domain(domain)
        if domain_config:
            benchmark_list = domain_config.benchmarks

    if not benchmark_list:
        click.echo("No benchmarks available for evaluation")
        return

    click.echo(f"Running {len(benchmark_list)} benchmarks...")
    # TODO: Implement benchmark evaluation
    click.echo("Benchmark evaluation not yet implemented")


@cli.command()
def list_domains():
    """List available domain configurations."""
    domain_mgr = DomainManager(str(CONFIG_DIR / "domains"))
    domains = domain_mgr.list_domains()

    if not domains:
        click.echo("No domains configured. Use 'lke init-domain' to create one.")
        return

    click.echo("Available domains:")
    for name in domains:
        domain = domain_mgr.get_domain(name)
        click.echo(f"\n  {name} (v{domain.version})")
        click.echo(f"    {domain.description[:60]}...")


@cli.command()
@click.argument('domain_name')
def interactive(domain_name):
    """Start an interactive extraction session."""
    # Load configuration
    config = _load_config()
    if not config:
        click.echo("Please run 'lke configure' first")
        return

    # Load domain
    domain_mgr = DomainManager(str(CONFIG_DIR / "domains"))
    domain = domain_mgr.get_domain(domain_name)

    if not domain:
        click.echo(f"Domain '{domain_name}' not found")
        return

    # Create LLM interface
    llm = create_llm_interface(config['provider'], **_get_llm_config(config))

    # Create interrogation engine
    engine = InterrogationEngine(llm=llm, domain=domain)

    click.echo(f"Starting interactive session for domain: {domain_name}")
    click.echo("Type 'help' for available commands, 'exit' to quit\n")

    while True:
        try:
            command = click.prompt('lke> ', type=str)

            if command.lower() in ['exit', 'quit']:
                break
            elif command.lower() == 'help':
                _show_interactive_help()
            elif command.lower().startswith('extract'):
                _interactive_extract(engine, domain)
            elif command.lower().startswith('analyze'):
                parts = command.split(maxsplit=1)
                if len(parts) > 1:
                    problem = parts[1]
                    # Get current concepts
                    result = engine.extract_knowledge()
                    analysis = engine.chain_of_thought_analysis(
                        problem,
                        result.raw_concepts
                    )
                    click.echo(f"\nAnalysis:\n{analysis}")
                else:
                    click.echo("Usage: analyze <problem description>")
            else:
                click.echo(f"Unknown command: {command}")

        except (EOFError, KeyboardInterrupt):
            click.echo("\nExiting...")
            break
        except Exception as e:
            click.echo(f"Error: {e}")


@cli.command()
def check_ollama():
    """Check Ollama installation and list available models."""
    try:
        from .interfaces.llm_interface import OllamaInterface

        ollama = OllamaInterface()
        if ollama.validate_connection():
            click.echo("✓ Ollama is running")

            models = ollama.list_models()
            if models:
                click.echo("\nAvailable models:")
                for model in models:
                    click.echo(f"  - {model}")
            else:
                click.echo("\nNo models installed. Run 'ollama pull <model>' to install one.")
        else:
            click.echo("✗ Ollama is not running. Start it with 'ollama serve'")
    except Exception as e:
        click.echo(f"✗ Error checking Ollama: {e}")


def _load_config() -> Optional[dict]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return None

    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def _get_llm_config(config: dict) -> dict:
    """Extract LLM-specific configuration."""
    llm_config = {
        'cache_dir': config.get('cache_dir')
    }

    if config['provider'] in ['claude-api', 'openai']:
        llm_config['api_key'] = config.get('api_key')

    if config['provider'] == 'ollama':
        llm_config['host'] = config.get('ollama_host', 'http://localhost:11434')

    if 'model' in config:
        llm_config['model'] = config['model']

    return llm_config


def _show_interactive_help():
    """Show help for interactive mode."""
    help_text = """
Available commands:
  extract           - Extract knowledge from the domain
  analyze <problem> - Analyze a problem using chain-of-thought
  help             - Show this help message
  exit/quit        - Exit interactive mode
"""
    click.echo(help_text)


def _interactive_extract(engine, domain):
    """Perform extraction in interactive mode."""
    click.echo("Extracting knowledge...")
    result = engine.extract_knowledge()

    extractor = StructureExtractor()
    model = extractor.extract_model(
        result,
        domain.name,
        domain.description
    )

    click.echo(f"\nExtracted {len(model.concepts)} concepts")
    click.echo("\nConcepts:")
    for concept in model.concepts[:5]:
        click.echo(f"  - {concept.name}: {concept.definition[:60]}...")

    if len(model.concepts) > 5:
        click.echo(f"  ... and {len(model.concepts) - 5} more")


if __name__ == '__main__':
    cli()