#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

version = '0.0.1'

setup(
    name='redis-clu',
    version=version,
    description='Redis Cluster Management Tool',
    long_description=open('README.md').read(),
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
