#!/usr/bin/env python3
"""
Simple example showing how to use the LLM wrapper.

This demonstrates the minimal viable product functionality:
- Connect to a local LLM using Ollama
- Connect using an API key (Claude, OpenAI)
- Generate responses from the LLM
"""

import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.dirname(__file__))

from lke.interfaces.llm_interface import create_llm_interface


def example_ollama():
    """Example: Using Ollama (local LLM)."""
    print("=" * 60)
    print("Example 1: Using Ollama (Local LLM)")
    print("=" * 60)

    # Create an Ollama interface
    # Note: Make sure Ollama is running with `ollama serve`
    # and you have a model installed with `ollama pull llama2`
    llm = create_llm_interface(
        "ollama",
        model="llama2",
        host="http://localhost:11434"
    )

    # Check if Ollama is available
    if not llm.validate_connection():
        print("⚠ Ollama is not running or model not available")
        print("  Start with: ollama serve")
        print("  Install model: ollama pull llama2")
        return

    print("✓ Connected to Ollama")

    # Generate a response
    prompt = "Explain what a neural network is in one sentence."
    print(f"\nPrompt: {prompt}")

    response = llm.generate(prompt)
    print(f"Response: {response.text}\n")


def example_claude_api():
    """Example: Using Claude API."""
    print("=" * 60)
    print("Example 2: Using Claude API")
    print("=" * 60)

    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set")
        print("  Set with: export ANTHROPIC_API_KEY=your_key")
        return

    # Create a Claude API interface
    llm = create_llm_interface(
        "claude-api",
        api_key=api_key,
        model="claude-3-haiku-20240307"
    )

    # Validate connection
    if not llm.validate_connection():
        print("✗ Failed to connect to Claude API")
        return

    print("✓ Connected to Claude API")

    # Generate a response
    prompt = "What is the capital of France?"
    print(f"\nPrompt: {prompt}")

    response = llm.generate(prompt, max_tokens=100)
    print(f"Response: {response.text}\n")


def example_openai_api():
    """Example: Using OpenAI API."""
    print("=" * 60)
    print("Example 3: Using OpenAI API")
    print("=" * 60)

    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("⚠ OPENAI_API_KEY not set")
        print("  Set with: export OPENAI_API_KEY=your_key")
        return

    # Create an OpenAI interface
    llm = create_llm_interface(
        "openai",
        api_key=api_key,
        model="gpt-3.5-turbo"
    )

    # Validate connection
    if not llm.validate_connection():
        print("✗ Failed to connect to OpenAI API")
        return

    print("✓ Connected to OpenAI API")

    # Generate a response
    prompt = "What is Python programming language?"
    print(f"\nPrompt: {prompt}")

    response = llm.generate(prompt, max_tokens=100)
    print(f"Response: {response.text}\n")


def example_with_caching():
    """Example: Using the caching feature."""
    print("=" * 60)
    print("Example 4: Using Cache (Mock LLM)")
    print("=" * 60)

    # Create a mock LLM with caching enabled
    llm = create_llm_interface(
        "mock",
        cache_dir="/tmp/lke_cache"
    )

    print("✓ Created mock LLM with caching")

    # First request (not cached)
    prompt = "Tell me a joke"
    print(f"\nFirst request: {prompt}")
    response1 = llm.generate(prompt)
    print(f"Response: {response1.text}")
    print(f"Cached: {response1.cached}")

    # Second request (should be cached)
    print(f"\nSecond request (same prompt): {prompt}")
    response2 = llm.generate(prompt)
    print(f"Response: {response2.text}")
    print(f"Cached: {response2.cached}\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("LLM Wrapper - Example Usage")
    print("=" * 60)
    print()

    # Run examples
    example_with_caching()
    example_ollama()
    example_claude_api()
    example_openai_api()

    print("=" * 60)
    print("Examples Complete!")
    print("=" * 60)
    print("\nNote: Some examples may be skipped if the required")
    print("      service is not available or API keys are not set.")


if __name__ == "__main__":
    main()
