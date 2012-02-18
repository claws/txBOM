#!/usr/bin/env python

"""
A distutils installation script for txBOM.
"""

from distutils.core import setup
import txbom


long_description = """txBOM is a Python Twisted package that allows you to iretrieve forecasts and observations
from the Australian Bureau of Meteorology.
Use it to integrate non blocking retrieval of Australian Bureau of Meteorology forecasts
and observations into your Python Twisted application.
"""

setup(name='txBOM',
      version='.'.join(txbom.version),
      description='txBOM is a Python Twisted package that allows you to iretrieve forecasts and observations from the Australian Bureau of Meteorology.',
      long_description=long_description,
      author='Chris Laws',
      author_email='clawsicus@gmail.com',
      license='http://www.opensource.org/licenses/mit-license.php',
      url='https://github.com/claws/txBOM',
      download_url='https://github.com/claws/txBOM/tarball/master',
      packages=['txbom'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Twisted']
      )




