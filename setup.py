# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Artron - multiprocessing with dependency graph and queue management allowing easy tool creation.

Licence
```````
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__author__ = "Ahmet Demir <me@ahmet2mir.eu>"

from setuptools import setup, find_packages

from artron.release import __version__

setup(
    name='artron',
    version=__version__,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ahmet2mir/python-artron.git',
    author='Ahmet Demir',
    author_email='me@ahmet2mir.eu',
    description='Artron - multiprocessing with dependency graph and queue management allowing easy tool creation.',
    license='License :: OSI Approved :: Apache Software License',
    keywords=['artron', 'multiprocessing', 'parallel'],
    packages=find_packages(),
    package_data = {'': ['README.md']}
)
