import os
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = 'Thumbor mongodb storage adapters'


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="thumbor_mongodb",
    version="1.0.0",
    author="ekapratama93",
    description=("Thumbor storage adapters for MongoDB"),
    license="MIT",
    keywords="thumbor mongodb mongo",
    url="https://github.com/ekapratama93/thumbor-mongodb",
    packages=find_packages(include=[
        'thumbor_mongodb',
        'thumbor_mongodb.mongodb',
        'thumbor_mongodb.storages',
        'thumbor_mongodb.result_storages'
    ]),
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'thumbor>=6.5.1,<7.0.0',
        'motor>=2.1.0,<3.0.0'
    ]
)
