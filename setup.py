#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

version = '0.0.2'

setup(
    name='redis-clu',
    version=version,
    description='Redis Cluster Management Tool',
    long_description=README,
    url='https://github.com/baranbartu/redis-clu',
    download_url='https://github.com/baranbartu/redis-clu/tarball/%s' % version,
    author='Baran Bartu Demirci',
    author_email='bbartu.demirci@gmail.com',
    license='MIT',
    keywords='redis cluster management replication master slave',
    packages=['redisclu'],
    entry_points={
        'console_scripts': ['redis-clu = redisclu.cli:main']
    },
    install_requires=[
        'hiredis',
        'redis',
        'futures==3.0.3',
    ]
)
