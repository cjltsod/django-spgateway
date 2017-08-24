from setuptools import setup

__version__ = "0.2.0"

with open('README.rst') as f:
    long_description = f.read()

setup(
    name="django-spgateway",
    version=__version__,
    description='Django support for Spgateway',
    keywords="django, spgateway",
    author="CJLTSOD <github.tsod@tsod.idv.tw>",
    author_email="github.tsod@tsod.idv.tw",
    url="https://github.com/cjltsod/django-spgateway",
    license="MIT",
    packages=["spgateway"],
    include_package_data=True,
    install_requires=["django>=1.10", "pycrypto>=2.6.1"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Framework :: Django :: 1.10",
        "Environment :: Web Environment",
    ],
    long_description=long_description,
)
