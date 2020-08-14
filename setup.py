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
    version="2.0.0",
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
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Multimedia :: Graphics :: Presentation",
    ],
    install_requires=[
        'thumbor>=7.0.0a5,<8.0.0',
        'motor>=2.1.0,<3.0.0'
    ]
)
