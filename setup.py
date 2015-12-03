import re
import ast
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.rst'), 'rb') as f:
    long_description = f.read()


_version_re = re.compile(r'__version__\s+=\s+(.*)')


with open('ruspost_soap/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(
    name='ruspost-soap-client',
    version=version,
    description='Implementation of Russian Post SOAP Tracking API',
    long_description=long_description,
    url='https://github.com/qnub/ru-post-soap-client',
    author='Vadim Lopatyuk',
    license='LGPL v3',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules'

        'Environment :: Other Environment',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',  # noqa

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='rupost ruspost tracking api',
    install_requires=['suds'],
    packages=find_packages(),
    include_package_data=True,
)
