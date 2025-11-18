#!/usr/bin/env python3
"""
Test script to demonstrate the LLM wrapper functionality.

This script shows how to use the LLM interfaces for:
1. Ollama (local LLM)
2. Claude API
3. OpenAI API
"""

import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.dirname(__file__))

from lke.interfaces.llm_interface import (
    create_llm_interface,
    OllamaInterface,
    ClaudeAPIInterface,
    OpenAIInterface,
    MockLLMInterface
)


def test_ollama():
    """Test Ollama interface."""
    print("=" * 60)
    print("Testing Ollama Interface")
    print("=" * 60)

    try:
        # Create Ollama interface (default: llama2)
        llm = OllamaInterface(model="llama2", host="http://localhost:11434")

        # Validate connection
        print("Validating Ollama connection...")
        if llm.validate_connection():
            print("✓ Ollama is running and model is available")

            # List available models
            models = llm.list_models()
            print(f"\nAvailable models: {', '.join(models)}")

            # Test a simple query
            print("\nTesting LLM query...")
            prompt = "What is 2 + 2? Answer in one sentence."
            response = llm.generate(prompt)
            print(f"Prompt: {prompt}")
            print(f"Response: {response.text}")
            print(f"Metadata: {response.metadata}")

        else:
            print("✗ Ollama is not running or model is not available")
            print("  Start Ollama with: ollama serve")
            print("  Pull a model with: ollama pull llama2")

    except Exception as e:
        print(f"✗ Error testing Ollama: {e}")
        print("  Make sure Ollama is installed and running")


def test_claude_api():
    """Test Claude API interface."""
    print("\n" + "=" * 60)
    print("Testing Claude API Interface")
    print("=" * 60)

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set in environment")
        print("  Set it with: export ANTHROPIC_API_KEY=your_key_here")
        print("  Skipping Claude API test")
        return

    try:
        # Create Claude API interface
        llm = ClaudeAPIInterface(api_key=api_key, model="claude-3-haiku-20240307")

        # Validate connection
        print("Validating Claude API connection...")
        if llm.validate_connection():
            print("✓ Claude API connection successful")

            # Test a simple query
            print("\nTesting LLM query...")
            prompt = "What is the capital of France? Answer in one sentence."
            response = llm.generate(prompt, max_tokens=100)
            print(f"Prompt: {prompt}")
            print(f"Response: {response.text}")
            print(f"Metadata: {response.metadata}")

        else:
            print("✗ Claude API connection failed")
            print("  Check your API key")

    except ImportError:
        print("✗ anthropic library not installed")
        print("  Install with: pip install anthropic")
    except Exception as e:
        print(f"✗ Error testing Claude API: {e}")


def test_openai_api():
    """Test OpenAI API interface."""
    print("\n" + "=" * 60)
    print("Testing OpenAI API Interface")
    print("=" * 60)

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("⚠ OPENAI_API_KEY not set in environment")
        print("  Set it with: export OPENAI_API_KEY=your_key_here")
        print("  Skipping OpenAI API test")
        return

    try:
        # Create OpenAI interface
        llm = OpenAIInterface(api_key=api_key, model="gpt-3.5-turbo")

        # Validate connection
        print("Validating OpenAI API connection...")
        if llm.validate_connection():
            print("✓ OpenAI API connection successful")

            # Test a simple query
            print("\nTesting LLM query...")
            prompt = "What is the speed of light? Answer in one sentence."
            response = llm.generate(prompt, max_tokens=100)
            print(f"Prompt: {prompt}")
            print(f"Response: {response.text}")
            print(f"Metadata: {response.metadata}")

        else:
            print("✗ OpenAI API connection failed")
            print("  Check your API key")

    except ImportError:
        print("✗ openai library not installed")
        print("  Install with: pip install openai")
    except Exception as e:
        print(f"✗ Error testing OpenAI API: {e}")


def test_mock_interface():
    """Test Mock interface."""
    print("\n" + "=" * 60)
    print("Testing Mock Interface")
    print("=" * 60)

    try:
        # Create mock interface
        llm = MockLLMInterface(responses={
            "test": "This is a test response",
            "hello": "Hello! How can I help you today?"
        })

        print("✓ Mock interface created")

        # Test queries
        print("\nTesting mock queries...")

        response1 = llm.generate("This is a test query")
        print(f"Query 1: This is a test query")
        print(f"Response: {response1.text}")

        response2 = llm.generate("Say hello to me")
        print(f"\nQuery 2: Say hello to me")
        print(f"Response: {response2.text}")

        response3 = llm.generate("Something else")
        print(f"\nQuery 3: Something else")
        print(f"Response: {response3.text}")

    except Exception as e:
        print(f"✗ Error testing Mock interface: {e}")


def test_factory():
    """Test the create_llm_interface factory function."""
    print("\n" + "=" * 60)
    print("Testing Factory Function")
    print("=" * 60)

    try:
        # Test creating different interfaces via factory
        print("Creating Ollama interface via factory...")
        ollama = create_llm_interface("ollama", model="llama2")
        print(f"✓ Created: {type(ollama).__name__}")

        print("\nCreating Mock interface via factory...")
        mock = create_llm_interface("mock")
        print(f"✓ Created: {type(mock).__name__}")

        print("\nFactory function works correctly!")

    except Exception as e:
        print(f"✗ Error testing factory: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM Wrapper Test Suite")
    print("=" * 60)
    print("\nThis script tests the LLM wrapper interfaces.")
    print("Make sure you have the required dependencies installed:\n")
    print("  - requests (for Ollama)")
    print("  - anthropic (for Claude API)")
    print("  - openai (for OpenAI API)")
    print()

    # Run tests
    test_factory()
    test_mock_interface()
    test_ollama()
    test_claude_api()
    test_openai_api()

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
