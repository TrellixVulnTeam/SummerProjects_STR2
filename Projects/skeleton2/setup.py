#!/usr/bin/env python


import bin


try:
    from setuptools import setup

except ImportError:
    from distutils.core import setup



config = {

    'description' : 'My Project',
    'author' : 'Bob Zhao',
    'url' : 'URL where the project is',
    'author_email' : 'zhao.f@wustl.edu',
    'version': '0.1',
    'install_requires' : ['nose'],
    'packages' : ['NAME'],
    'scripts' : [],
    'name' : 'projectname'

}





