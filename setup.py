#!/usr/bin/env python3
"""
Setup script for Latent Knowledge Explorer.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="latent-knowledge-explorer",
    version="0.1.0",
    author="LKE Team",
    author_email="",
    description="Extract structured scientific understanding from Large Language Models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/johnjanik/LatentKnowledgeExplorer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=3.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
        ],
        "ollama": [
            "requests>=2.28",
        ],
        "api": [
            "anthropic>=0.7",
            "openai>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lke=lke.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "lke": [
            "examples/*.yaml",
            "examples/*.json",
        ],
    },
    zip_safe=False,
)