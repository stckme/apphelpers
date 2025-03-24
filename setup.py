#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

# type: ignore

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.rst") as history_file:
    history = history_file.read()

requirements = ["loguru", "google-auth"]

setup_requirements = []

test_requirements = []

setup(
    author="Scroll Tech",
    author_email="tech@scrollstack.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Common helper libraries for Python Apps",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="apphelpers",
    name="apphelpers",
    packages=find_packages(exclude=["tests"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/scrolltech/apphelpers",
    version="0.97.1",
    zip_safe=False,
)
