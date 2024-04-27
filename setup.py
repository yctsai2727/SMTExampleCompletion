# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='LTL',
    version='0.1.0',
    description='Learn Model with LTL',
    long_description=readme,
    author='Mrudula Balachander',
    author_email='mrudula.balachander@ulb.be',
    url='https://github.com/mrudu/acacia-bonsai-python',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

