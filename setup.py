from setuptools import setup

__version__ = "0.4.0"

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
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Framework :: Django :: 2.1",
        "License :: OSI Approved :: MIT License",
        "Environment :: Web Environment",
    ],
    long_description=long_description,
)
