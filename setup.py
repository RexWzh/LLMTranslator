#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [ 'chattool>=2.0' ]

test_requirements = ['pytest>=3', ]

setup(
    author="Rex Wang",
    author_email='1073853456@qq.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Text translator using OpenAI-like API.",
    entry_points={
        'console_scripts': [
            'llmtranslator=llmtranslator.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='llmtranslator',
    name='llmtranslator',
    packages=find_packages(include=['llmtranslator', 'llmtranslator.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/RexWzh/llmtranslator',
    version='0.0.1',
    zip_safe=False,
)
