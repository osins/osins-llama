from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="llama-cli",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A CLI tool for managing and running LLM models with llama_cpp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/llama",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["llama", "llama.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click~=8.1.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "llama=llama.main:cli",
        ],
    },
)