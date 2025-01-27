# Copyright 2015-2017 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function, unicode_literals

from setuptools import setup, find_packages
import os

# *Any* updates here should also go into c7n_mailer/deploy.py for lambda packaging.
requires = [
    "Jinja2",
    "boto3",
    "jsonschema",
    "ruamel.yaml==0.15.42",
    "datadog",
    "slackclient",
    "sendgrid",
    "ldap3"]

try:
    from concurrent import futures  # noqa F401
except ImportError:
    # The backport has SyntaxErrors under py36, so avoid installing it.
    # https://github.com/agronholm/pythonfutures/issues/41
    requires += ['futures']

description = ""
if os.path.exists('README.md'):
    description = open('README.md').read()

setup(
    name="c7n_mailer",
    version='0.3.1',
    description="Cloud Custodian - Reference Mailer",
    long_description=description,
    classifiers=[
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Distributed Computing"
    ],
    url="https://github.com/capitalone/cloud-custodian",
    license="Apache-2.0",
    packages=find_packages('c7n_mailer'),
    entry_points={
        'console_scripts': [
            'c7n-mailer = c7n_mailer.cli:main',
            'c7n-mailer-replay = c7n_mailer.replay:main'
        ]
    },
    install_requires=requires,
)
