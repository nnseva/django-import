try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from django_import.version import __version__ as version

with open("README.rst", "r") as fp:
    description = fp.read() + "\n"

setup(
    name="django-import",
    version=version,
    description="Import to django models",
    long_description=description,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Development Status :: Beta',
        "Framework :: Django",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    ],
    keywords="CSV JSON TSV import django fixture",
    license='LGPL',
    packages=["django_import"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "django",
        "pandas",
        "django-jsoneditor",
        "django-extensions",
        "markdown",
        "six",
        "xlrd>=1.0.0"
    ],
)
