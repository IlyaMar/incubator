"""
Setup script for go-to-jinja.
"""

from setuptools import setup, find_packages

setup(
    name="go-to-jinja",
    version="0.1.0",
    description="Convert Go text templates to Jinja templates",
    author="Your Name",
    author_email="your.email@example.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "jinja2>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "go-to-jinja=go_to_jinja.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)