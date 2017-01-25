#!/usr/bin/env python
import os
from codecs import open
from setuptools import setup, find_packages
import imp

here = os.path.abspath(os.path.dirname(__file__))
__version__ = imp.load_source('modispds.version', 'modispds/version.py').__version__

# get the dependencies and installs
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    reqa = f.read().split('\n')
install_requires = [x.strip() for x in reqa if 'git+' not in x]

fname = os.path.join(here, 'requirements-dev.txt')
if os.path.exists(fname):
    with open(os.path.join(here, 'requirements-dev.txt'), encoding='utf-8') as f:
        reqs = f.read().split('\n')
    tests_require = [x.strip() for x in reqs if 'git+' not in x]
else:
    tests_require = []

console_scripts = [
    'modis-pds = modispds.core:cli'
]

setup(
    name='modispds',
    version=__version__,
    author='Drew Bollinger (drewbo), Matthew Hanson (matthewhanson)',
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
    entry_points={'console_scripts': console_scripts},
    install_requires=install_requires,
    tests_require=tests_require,
)
