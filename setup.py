# SPDX-License-Identifier: Apache-2.0

from setuptools import setup
from pathlib import Path


def readme():
    with open('README.md') as f:
        return f.read()

def requirements():
    return Path('requirements.txt').read_text().splitlines()


setup(
    name="AIPL",
    version="0.1",
    description="A tiny DSL to make it easier to explore and experiment with AI pipelines.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    py_modules=["aipl"],
    scripts=['bin/aipl'],
    install_requires=requirements(),
    packages=find_packages(),
    author="Saul Pwanson",
    url="https://github.com/saulpw/aipl",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
    keywords="GPT aipl visidata array",
)
