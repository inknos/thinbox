#!/usr/bin/python3


from distutils.core import setup
from setuptools import setup, find_packages


setup(
    name='thinbox',
    version='0.1.0',
    description='Thinbox rewrittein in pyhton',
    author='Nicola Sella',
    author_email='nsella@redhat.com',
    url='https://github.com/inknos/thinbox_py',
    packages=find_packages(include=['thinbox', 'thinbox.*']),
    scripts=[
        "bin/thinbox",
    ],
)
