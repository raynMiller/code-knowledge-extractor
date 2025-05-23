import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pykb",
    version="0.1.0",
    author="AI Assistant",
    author_email="assistant@example.com",
    description="A Python tool to create a knowledge base from Python projects.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://localhost/pykb",  # Placeholder URL
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        # No external dependencies for now, as ast, argparse, json, os, glob, fnmatch are standard.
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'pykb=pykb.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",  # Assuming MIT License
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha", # Initial development stage
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
    ],
)
