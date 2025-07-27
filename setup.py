"""Setup configuration for Code-Sitter package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="code-sitter",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-time syntax-aware code indexing and search for TypeScript",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-sitter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "cocoindex>=0.1.0",
        "python-dotenv>=1.0.0",
        "sentence-transformers>=2.2.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.2.0",
        "aiofiles>=23.0.0",
        "watchdog>=3.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "tree-sitter>=0.20.0",
        "tree-sitter-languages>=1.8.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "code-sitter=cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
