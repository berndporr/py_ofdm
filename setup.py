#!/usr/bin/python3

from setuptools import setup

with open('README_pypi.rst') as f:
    long_description = f.read()

setup(
    name='pyofdm',
    version='2.1.1',
    description="OFDM transmitter and receiver",
    long_description=long_description,
    author='Bernd Porr, David Hutchings',
    author_email='mail@berndporr.me.uk, David.Hutchings@glasgow.ac.uk',
    packages=['pyofdm'],
    include_package_data=True,
    install_requires=['komm'],
    zip_safe=False,
    url='https://github.com/dchutchings/py_ofdm',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)
