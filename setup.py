import codecs
import os
import re

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


dynamic_version = find_version("vimx", "__init__.py")

setup(
    name="vimx",
    version=dynamic_version,
    author="Alfredo Sequeida",
    description="Vimx aims to be a crossplaform vimium-like application for your entire desktop",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlfredoSequeida/vimx",
    download_url="https://github.com/AlfredoSequeida/vimx/archive/"
    + dynamic_version
    + ".tar.gz",
    keywords="vimx vimium mouseless keybaordnaviation",
    platforms="any",
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 8",
        "Operating System :: Microsoft :: Windows :: Windows 8.1",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: Desktop Environment",
    ],
    license="MIT",
    packages=[
        "vimx",
        "vimx.platform_utils",
        "vimx.backends",
        "vimx.hud",
    ],
    include_package_data=True,
    install_requires=["PyGObject"],
    entry_points={"console_scripts": ["vimx = vimx.vimx:main"]},
)