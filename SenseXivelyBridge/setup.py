#!/usr/bin/env python

from distutils.core import setup

setup(name='SenseXivelyBridge',
      version='1.1',
      description='Sense-Xively Bridge',
      author='Arosha Bandara and Neil Smith',
      author_email='arosha.bandara@open.ac.uk',
      url='http://sense.open.ac.uk',
      packages=['OUSense'],
      package_dir={'OUSense' : 'src/OUSense'},
      data_files=[('lib', ['xively_python-0.1.0_rc2-py3.3.egg'])]
     )
