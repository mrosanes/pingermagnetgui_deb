#!/usr/bin/env python 
# Always prefer setuptools over distutils

from setuptools import setup, find_packages 

__doc__ = """ 

To install as system package:  

    python setup.py install   
    
To install as local package:   

    RU=/opt/control
    python setup.py egg_info --egg-base=tmp install --root=$RU/files --no-compile \
    --install-lib=lib/python/site-packages --install-scripts=ds
    
------------------------------------------------------------------------------- 
"""
print(__doc__)

# The version is updated automatically with bumpversion
# Do not update manually
__version = '1.8.1'

__license = 'GPL-3.0' 


setup(
    name = 'PingerMagnetGUI',
    version = __version,
    license = __license,
    author='Manolo Broseta',
    author_email='mbroseta@cells.es',
    maintainer='ct4',
    maintainer_email='ct4@cells.es',
    packages=find_packages(),
    entry_points = {
        'console_scripts': 
            [
            'ctdipinger = PingerMagnetGUI.gui_pinger:main',
            ]
        },
    keywords='GUI',
    include_package_data = True,
    description = 'GUI to control H/V Pinger Magnets',
    long_description = "GUI to control Horizontal and Vertical Pinger Magnets",
    classifiers=['Development Status :: 5 - Production',
                'Intended Audience :: Science/Research',
                'License :: OSI Approved :: '
                'GNU General Public License v3 or later (GPLv3+)',
                'Programming Language :: Python',
                'Topic :: Scientific/Engineering :: '
                ''],
    url='https://git.cells.es/controls/PingerMagnetGUI',
    )
