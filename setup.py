"""uWeb3 installer."""

import os
import re
from setuptools import setup, find_packages

REQUIREMENTS = [
  'PyMySQL',
  'pytz'
]

#  'sqlalchemy',
#  'werkzeug',

def description():
  with open(os.path.join(os.path.dirname(__file__), 'README.md')) as r_file:
    return r_file.read()


def version():
  main_lib = os.path.join(os.path.dirname(__file__), 'uweb3', '__init__.py')
  with open(main_lib) as v_file:
    return re.match(".*__version__ = '(.*?)'", v_file.read(), re.S).group(1)


setup(
    name='uWeb3',
    version=version(),
    description='uWeb, python3, uswgi compatible micro web platform',
    long_description = 'file: README.md',
    long_description_content_type = 'text/markdown',
    license='ISC',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ],
    author='Jan Klopper',
    author_email='jan@underdark.nl',
    url='https://github.com/underdark.nl/uweb3',
    keywords='minimal python web framework',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    python_requires='>=3.5')
