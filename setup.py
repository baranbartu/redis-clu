#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='redis-clu',
    version='0.0.1',
    description='Redis Cluster Management Tool',
    long_description=open('README.md').read(),
    url='https://github.com/baranbartu/redis-clu',
    author='baranbartu',
    author_email='bbartu.demirci@gmail.com',
    license='MIT',
    keyswords='redis cluster management replication master slave',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['redis-clu = redisclu.cli:main']
    },
    install_requires=[
        'hiredis',
        'redis',
        'futures==3.0.3',
    ]
)
