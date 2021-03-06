#!/usr/bin/python3


from distutils.core import setup
from setuptools import setup, find_packages


setup(
    name='thinbox',
    version='0.4.0',
    description='Thinbox rewrittein in pyhton',
    author='Nicola Sella',
    author_email='nsella@redhat.com',
    url='https://github.com/inknos/thinbox',
    packages=find_packages(include=['thinbox', 'thinbox.*']),
    scripts=[
        "bin/thinbox",
    ],
    install_requires=[
        "scp",
        "argcomplete",
        "beautifulsoup4",
        "requests",
        "paramiko",
    ]
)
