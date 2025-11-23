# Copyright 2025 Charles Shaw
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Install script for Optimized Supergeo Design (OSD) package."""

from setuptools import setup, find_packages

__version__ = '0.1.0'

PROJECT_NAME = 'osd'

REQUIRED_PACKAGES = [
    'numpy>=1.20.0',
    'pandas>=1.3.0',
    'scipy>=1.9.0',  # Required for scipy.optimize.milp
    'scikit-learn>=1.0.0',
    'matplotlib>=3.4.0',
    'seaborn>=0.11.0',
    'tqdm>=4.60.0',
]

DEV_PACKAGES = [
    'pytest>=7.0.0',
    'pytest-cov>=3.0.0',
    'black>=22.0.0',
    'flake8>=4.0.0',
    'mypy>=0.950',
]

setup(
    name=PROJECT_NAME,
    version=__version__,
    description='Optimized Supergeo Design (OSD) - A scalable framework for balanced geographic experiments',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Charles Shaw',
    author_email='charles@fixedpoint.io',
    url='https://github.com/shawcharles/osd',
    # Contained modules and scripts.
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=REQUIRED_PACKAGES,
    extras_require={
        'dev': DEV_PACKAGES,
    },
    python_requires='>=3.8',
    # PyPI package information.
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    license='Apache 2.0',
    keywords='experimental-design causal-inference marketing-science optimization pca geographic-experiments supergeo',
)
