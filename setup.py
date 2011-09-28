#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import find_packages, setup

curdir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = 'watchconf',
    description = 'compare configuration between servers',
    license = 'http://www.gnu.org/licenses/gpl-2.0.html',
    version = '1.0',
    author = 'Òscar Vilaplana',
    author_email = 'dev@oscarvilaplana.cat',
    url = '',
    install_requires = ['paramiko', 'flask', 'flask-cache', 'opster'],
    packages=find_packages(curdir),
    entry_points = {'console_scripts': ['watchconf=watchconf:run.command', ]},
    )
