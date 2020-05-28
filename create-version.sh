#!/bin/sh

version=$1
shift 1
desc=$*

echo "VERSION:" $version >&2
echo __version__ = \"$version\" >django_import/version.py

git commit -a -m "$*"
git tag $version -a -m "$*"

exit 0
