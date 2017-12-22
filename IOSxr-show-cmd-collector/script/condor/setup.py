#! /usr/bin/python
# Copyright (c) 2011 by cisco Systems, Inc.
# All rights reserved.

"""
 Installation script for accelerated upgrade
"""
import codecs
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command


VERSION = '0.0.2'
DESCRIPTION = 'Condor module for IOS XR connection handling and ' \
              'command execution'
with codecs.open('README.rst', 'r', encoding='UTF-8') as readme:
    LONG_DESCRIPTION = ''.join(readme)

CLASSIFIERS = [
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
]

packages = [
    'condor',
    'condor.controllers',
    'condor.controllers.protocols',
    'condor.platforms',
]

NAME = 'condor'

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Klaudiusz Staniek',
    author_email='klstanie [at] cisco.com',
    url='',
    tests_require=['tox', 'pytest'],
    platforms=[ 'any' ],
    packages=packages,
    install_requires=['pexpect>=3.1',
                      'keyring'],
    classifiers=CLASSIFIERS,
    zip_safe=True
)
