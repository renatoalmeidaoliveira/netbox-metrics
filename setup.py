import codecs
import os.path

from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name = "netbox-metrics",
    version=get_version('netbox_metrics_ext/version.py'),
    description = "Plugin to improve the instrumentation of NetBox and expose additional metrics (Application Metrics, RQ Worker).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/renatoalmeidaoliveira/nbrisk',
    author='Renato Almdida Oliveira',
    author_email='renato.almeida.oliveira@gmail.com',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ]
)
