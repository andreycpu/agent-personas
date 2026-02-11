"""
Setup script for the Agent Personas framework.
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

# Read version from __init__.py
version_file = here / "agent_personas" / "__init__.py"
version_line = [line for line in version_file.read_text().split('\n') if line.startswith('__version__')][0]
version = version_line.split('"')[1]

setup(
    name="agent-personas",
    version=version,
    description="A comprehensive framework for defining and managing AI agent personalities and behaviors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andreycpu/agent-personas",
    author="Agent Personas Contributors",
    author_email="contact@example.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai, personas, personality, behavior, agents, nlp, conversation, emotions",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies - keeping minimal for maximum compatibility
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "examples": [
            "jupyter",
            "matplotlib",
            "pandas",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinx-autodoc-typehints",
        ],
    },
    package_data={
        "agent_personas": [
            "examples/*.json",
            "examples/*.py",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-personas=agent_personas.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/andreycpu/agent-personas/issues",
        "Source": "https://github.com/andreycpu/agent-personas",
        "Documentation": "https://agent-personas.readthedocs.io/",
    },
)