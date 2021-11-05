#!/usr/bin/python3


from distutils.core import setup


setup(
    name='thinbox',
    version='0.1.0',
    description='Thinbox rewrittein in pyhton',
    author='Nicola Sella',
    author_email='nsella@redhat.com',
    url='https://github.com/inknos/thinbox_py',
    scripts=[
        "thinbox.py",
    ],
)
