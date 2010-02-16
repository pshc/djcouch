#!/usr/bin/env python

from distutils.core import setup

setup(name='djcouch',
      version='0.1',
      description='Django-CouchDB helper',
      author='Paul Collier',
      author_email='pshcolli@uwaterloo.ca',
      url='http://github.com/pshc/djcouch',
      packages=['djcouch'],
      requires=['django', 'couchdb'])

