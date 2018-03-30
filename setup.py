#!/usr/bin/env python
import os
from codecs import open
from setuptools import setup, find_packages
import imp
import io

here = os.path.abspath(os.path.dirname(__file__))
__version__ = imp.load_source('modispds.version', 'modispds/version.py').__version__

# get the dependencies and installs
with io.open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if 'git+' not in x]

console_scripts = [
    'modis-pds = modispds.main:cli'
]
print(install_requires)
setup(
    name='modispds',
    version=__version__,
    author='Matthew Hanson (matthewhanson), Drew Bollinger (drewbo)',
    description='Get MODIS data, convert to single band GeoTIFFs, and upload to S3',
    url='https://github.com/AstroDigital/modis-ingestor',
    license='MIT',
    classifiers=[
        'Framework :: Pytest',
        'Topic :: Scientific/Engineering :: GIS',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: Freeware',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=['docs', 'test']),
    include_package_data=True,
    entry_points={'console_scripts': console_scripts}
)
