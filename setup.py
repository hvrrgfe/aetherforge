"""AetherForge - AI-Native Game Creation & Runtime System"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="aetherforge",
    version="2.0.0",
    description="AI-Native Game Creation & Runtime System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AetherForge Team",
    packages=find_packages(include=["aetherforge", "aetherforge.*"]),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "flask>=3.0",
        "mcp>=1.0",
        "pyyaml>=6.0",
        "Pillow>=10.0",
        "numpy>=1.24",
    ],
    extras_require={
        "physics": ["pymunk>=7.0"],
        "audio": ["pygame>=2.5"],
        "image-gen": ["torch>=2.0", "diffusers>=0.24", "transformers>=4.36"],
        "music-gen": ["torch>=2.0"],
        "full": [
            "pymunk>=7.0",
            "pygame>=2.5",
            "torch>=2.0",
            "diffusers>=0.24",
            "transformers>=4.36",
        ],
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "aetherforge=aetherforge.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)