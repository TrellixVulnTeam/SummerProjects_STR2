# (c) 2012-2016 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.
'''
We use the following conventions in this module:

    dist:        canonical package name, e.g. 'numpy-1.6.2-py26_0'

    ROOT_PREFIX: the prefix to the root environment, e.g. /opt/anaconda

    PKGS_DIR:    the "package cache directory", e.g. '/opt/anaconda/pkgs'
                 this is always equal to ROOT_PREFIX/pkgs

    prefix:      the prefix of a particular environment, which may also
                 be the root environment

Also, this module is directly invoked by the (self extracting) tarball
installer to create the initial environment, therefore it needs to be
standalone, i.e. not import any other parts of `conda` (only depend on
the standard library).
'''
import os
import re
import sys
import json
import shutil
import stat
from os.path import abspath, dirname, exists, isdir, isfile, islink, join
from optparse import OptionParser


on_win = bool(sys.platform == 'win32')
try:
    FORCE = bool(int(os.getenv('FORCE', 0)))
except ValueError:
    FORCE = False

LINK_HARD = 1
LINK_SOFT = 2  # never used during the install process
LINK_COPY = 3
link_name_map = {
    LINK_HARD: 'hard-link',
    LINK_SOFT: 'soft-link',
    LINK_COPY: 'copy',
}
SPECIAL_ASCII = '$!&\%^|{}[]<>~`"\':;?@*#'

# these may be changed in main()
ROOT_PREFIX = sys.prefix
PKGS_DIR = join(ROOT_PREFIX, 'pkgs')
SKIP_SCRIPTS = False
IDISTS = {
  "alabaster-0.7.10-py27_0": {
    "md5": "18fd72549b202d626b578281d282293b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/alabaster-0.7.10-py27_0.tar.bz2"
  }, 
  "anaconda-4.4.0-np112py27_0": {
    "md5": "02d10caa1af42449a6abb9214ee41d7b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/anaconda-4.4.0-np112py27_0.tar.bz2"
  }, 
  "anaconda-client-1.6.3-py27_0": {
    "md5": "67d1b9efc4b7ae1bcdd66151ae38b879", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/anaconda-client-1.6.3-py27_0.tar.bz2"
  }, 
  "anaconda-project-0.4.1-py27_0": {
    "md5": "87e1ac10e028e9bf60670c925d3e7d3a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/anaconda-project-0.4.1-py27_0.tar.bz2"
  }, 
  "asn1crypto-0.22.0-py27_0": {
    "md5": "8cfb8276c9ebcf4ecbf583da49733bca", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/asn1crypto-0.22.0-py27_0.tar.bz2"
  }, 
  "astroid-1.4.9-py27_0": {
    "md5": "3c1e95a928cb3bebc2aa698a7ecac2ab", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/astroid-1.4.9-py27_0.tar.bz2"
  }, 
  "astropy-1.3.2-np112py27_0": {
    "md5": "069a9cd9858bf77ddbc51a9d91dc01c2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/astropy-1.3.2-np112py27_0.tar.bz2"
  }, 
  "babel-2.4.0-py27_0": {
    "md5": "a5c124c70870b7e7b52f5c835b4f103a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/babel-2.4.0-py27_0.tar.bz2"
  }, 
  "backports-1.0-py27_0": {
    "md5": "076e2d4710a2d7815b16147962c8a238", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/backports-1.0-py27_0.tar.bz2"
  }, 
  "backports_abc-0.5-py27_0": {
    "md5": "c02bb768758fc3ccfa5cf03e36a7f14a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/backports_abc-0.5-py27_0.tar.bz2"
  }, 
  "beautifulsoup4-4.6.0-py27_0": {
    "md5": "5da85fdde3ae74bf7b5164888ec8b9b2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/beautifulsoup4-4.6.0-py27_0.tar.bz2"
  }, 
  "bitarray-0.8.1-py27_0": {
    "md5": "08fc3351d6e4d5c7c390a1c2f893e2ec", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/bitarray-0.8.1-py27_0.tar.bz2"
  }, 
  "bleach-1.5.0-py27_0": {
    "md5": "c9546fae04861ab133ef2121b330a1e9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/bleach-1.5.0-py27_0.tar.bz2"
  }, 
  "bokeh-0.12.5-py27_0": {
    "md5": "be6335fa8fb61c7811ac83fc14a9069e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/bokeh-0.12.5-py27_0.tar.bz2"
  }, 
  "boto-2.46.1-py27_0": {
    "md5": "8a1ece09868cf07700163df0c567722b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/boto-2.46.1-py27_0.tar.bz2"
  }, 
  "bottleneck-1.2.1-np112py27_0": {
    "md5": "20af77885c164619877a575966dde541", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/bottleneck-1.2.1-np112py27_0.tar.bz2"
  }, 
  "cairo-1.14.8-0": {
    "md5": "51fd93aac702973313a29049317e8ef8", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cairo-1.14.8-0.tar.bz2"
  }, 
  "cdecimal-2.3-py27_2": {
    "md5": "b8abb3ae541e4edf0e0d95ac39eac1dc", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cdecimal-2.3-py27_2.tar.bz2"
  }, 
  "cffi-1.10.0-py27_0": {
    "md5": "c774ed034eb0c8a062eee32c956c8ded", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cffi-1.10.0-py27_0.tar.bz2"
  }, 
  "chardet-3.0.3-py27_0": {
    "md5": "53609155449178bdeb5711aabdd5b69d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/chardet-3.0.3-py27_0.tar.bz2"
  }, 
  "chest-0.2.3-py27_0": {
    "md5": "08d95dc8e7912b711917eab28ddfaf97", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/chest-0.2.3-py27_0.tar.bz2"
  }, 
  "click-6.7-py27_0": {
    "md5": "155caacae5d8d7a98a46fd143b970c23", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/click-6.7-py27_0.tar.bz2"
  }, 
  "cloudpickle-0.2.2-py27_0": {
    "md5": "4ccc810105666d9fe4da6e293cb73f12", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cloudpickle-0.2.2-py27_0.tar.bz2"
  }, 
  "clyent-1.2.2-py27_0": {
    "md5": "b13bd65e9e49f3b8402197e1ea05e664", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/clyent-1.2.2-py27_0.tar.bz2"
  }, 
  "colorama-0.3.9-py27_0": {
    "md5": "73a8de2d212f7b20f84416adf40c4771", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/colorama-0.3.9-py27_0.tar.bz2"
  }, 
  "conda-4.3.18-py27_0": {
    "md5": "5c8247b4bd40304a339fd6d643ee091d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/conda-4.3.18-py27_0.tar.bz2"
  }, 
  "conda-env-2.6.0-0": {
    "md5": "3aa23759211de62f6daa4981032c7c55", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/conda-env-2.6.0-0.tar.bz2"
  }, 
  "configobj-5.0.6-py27_0": {
    "md5": "1bdd4cde87fc0efa4728c07322fd3fed", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/configobj-5.0.6-py27_0.tar.bz2"
  }, 
  "configparser-3.5.0-py27_0": {
    "md5": "a838852f25ccbc6a98cca5e3c914d1da", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/configparser-3.5.0-py27_0.tar.bz2"
  }, 
  "contextlib2-0.5.5-py27_0": {
    "md5": "dea4b0947c8e642dcdbf22d9d39d5ba6", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/contextlib2-0.5.5-py27_0.tar.bz2"
  }, 
  "cryptography-1.8.1-py27_0": {
    "md5": "e51b3d8d8d027c92d284c28ca79e2d97", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cryptography-1.8.1-py27_0.tar.bz2"
  }, 
  "curl-7.52.1-0": {
    "md5": "e759f201b9dc488b8441f3f4228657a2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/curl-7.52.1-0.tar.bz2"
  }, 
  "cycler-0.10.0-py27_0": {
    "md5": "9d1b54c79de8294644ecb0508db16beb", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cycler-0.10.0-py27_0.tar.bz2"
  }, 
  "cython-0.25.2-py27_0": {
    "md5": "f177eb242b99b58c83a7fc19280752bd", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cython-0.25.2-py27_0.tar.bz2"
  }, 
  "cytoolz-0.8.2-py27_0": {
    "md5": "8f983dfde614a17376b32e49ba1edc14", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/cytoolz-0.8.2-py27_0.tar.bz2"
  }, 
  "dask-0.14.3-py27_0": {
    "md5": "ff456206a982a30fb73566ddfc479b6e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/dask-0.14.3-py27_0.tar.bz2"
  }, 
  "datashape-0.5.4-py27_0": {
    "md5": "8dbbc5f6ab3e88f84d94f9fc21bdd347", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/datashape-0.5.4-py27_0.tar.bz2"
  }, 
  "decorator-4.0.11-py27_0": {
    "md5": "e0b288e4b1d2eeee4d139b58f6dfe871", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/decorator-4.0.11-py27_0.tar.bz2"
  }, 
  "distributed-1.16.3-py27_0": {
    "md5": "d11b6b7eb336778f41a2d49128686400", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/distributed-1.16.3-py27_0.tar.bz2"
  }, 
  "docutils-0.13.1-py27_0": {
    "md5": "14dd9bc07536e8dfea9786ca3d6176ff", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/docutils-0.13.1-py27_0.tar.bz2"
  }, 
  "entrypoints-0.2.2-py27_1": {
    "md5": "c2d87bc8fdd0a3baf328769b46a0625b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/entrypoints-0.2.2-py27_1.tar.bz2"
  }, 
  "enum34-1.1.6-py27_0": {
    "md5": "00ffde7f3be1d890f93f065a079aee68", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/enum34-1.1.6-py27_0.tar.bz2"
  }, 
  "et_xmlfile-1.0.1-py27_0": {
    "md5": "771d1a28cc8c5fd4081fc5954c877271", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/et_xmlfile-1.0.1-py27_0.tar.bz2"
  }, 
  "expat-2.1.0-0": {
    "md5": "77ad9455bd1c3e4d7cb0693b87f4241f", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/expat-2.1.0-0.tar.bz2"
  }, 
  "fastcache-1.0.2-py27_1": {
    "md5": "1eb737927c08346eea0a4f01c3225cf9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/fastcache-1.0.2-py27_1.tar.bz2"
  }, 
  "flask-0.12.2-py27_0": {
    "md5": "f836eefc0a00300fda192fb086abbd07", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/flask-0.12.2-py27_0.tar.bz2"
  }, 
  "flask-cors-3.0.2-py27_0": {
    "md5": "504925d2c17610b3fda9828c2d2c374d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/flask-cors-3.0.2-py27_0.tar.bz2"
  }, 
  "fontconfig-2.12.1-3": {
    "md5": "a96db02867f5bf62905baccdd2b39d1d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/fontconfig-2.12.1-3.tar.bz2"
  }, 
  "freetype-2.5.5-2": {
    "md5": "9f983cbddb082fba43ff7a4744dbf526", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/freetype-2.5.5-2.tar.bz2"
  }, 
  "funcsigs-1.0.2-py27_0": {
    "md5": "a0c776819d78e8d152290b6d3c7b78bd", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/funcsigs-1.0.2-py27_0.tar.bz2"
  }, 
  "functools32-3.2.3.2-py27_0": {
    "md5": "cb37fb70ca02d23d77470d6f8f3b4a3b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/functools32-3.2.3.2-py27_0.tar.bz2"
  }, 
  "futures-3.1.1-py27_0": {
    "md5": "96df4a01476edce6b1f3f3eb3e69b77f", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/futures-3.1.1-py27_0.tar.bz2"
  }, 
  "get_terminal_size-1.0.0-py27_0": {
    "md5": "f981ae41302d3669571277b150eecd33", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/get_terminal_size-1.0.0-py27_0.tar.bz2"
  }, 
  "gevent-1.2.1-py27_0": {
    "md5": "7db87cbad866b46aebb7439ea369427c", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/gevent-1.2.1-py27_0.tar.bz2"
  }, 
  "greenlet-0.4.12-py27_0": {
    "md5": "9d478bea2443f00f5a79afea9242fa87", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/greenlet-0.4.12-py27_0.tar.bz2"
  }, 
  "grin-1.2.1-py27_3": {
    "md5": "dea4c8a336b54e21dbcfd810b486d780", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/grin-1.2.1-py27_3.tar.bz2"
  }, 
  "h5py-2.7.0-np112py27_0": {
    "md5": "4aab854d9ec14c90af3adcbaaf835a8a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/h5py-2.7.0-np112py27_0.tar.bz2"
  }, 
  "hdf5-1.8.17-1": {
    "md5": "fcfbf984d8d4c5c71c82568b9a764b5e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/hdf5-1.8.17-1.tar.bz2"
  }, 
  "heapdict-1.0.0-py27_1": {
    "md5": "4e1bf72e57904227d5d865a3bc1b2c81", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/heapdict-1.0.0-py27_1.tar.bz2"
  }, 
  "html5lib-0.999-py27_0": {
    "md5": "91741b23839ad928ca40b6bed1c180b4", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/html5lib-0.999-py27_0.tar.bz2"
  }, 
  "idna-2.5-py27_0": {
    "md5": "c50e15dc445978aed5be3b61273979ce", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/idna-2.5-py27_0.tar.bz2"
  }, 
  "imagesize-0.7.1-py27_0": {
    "md5": "afc252bb976ab8abecb5b4929e6fb3d2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/imagesize-0.7.1-py27_0.tar.bz2"
  }, 
  "ipaddress-1.0.18-py27_0": {
    "md5": "12f96f52c27f9b0f6d02ad0b108f63c9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ipaddress-1.0.18-py27_0.tar.bz2"
  }, 
  "ipykernel-4.6.1-py27_0": {
    "md5": "9e68e3c2fd937bab3463322afcacbe13", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ipykernel-4.6.1-py27_0.tar.bz2"
  }, 
  "ipython-5.3.0-py27_0": {
    "md5": "72d33eff851a01dd039df707bc6d7110", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ipython-5.3.0-py27_0.tar.bz2"
  }, 
  "ipython_genutils-0.2.0-py27_0": {
    "md5": "1d268cc72f4fc8a1b77e6ed63225263b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ipython_genutils-0.2.0-py27_0.tar.bz2"
  }, 
  "ipywidgets-6.0.0-py27_0": {
    "md5": "a7c197a5178beb6e066a881e3d92423f", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ipywidgets-6.0.0-py27_0.tar.bz2"
  }, 
  "isort-4.2.5-py27_0": {
    "md5": "a49f6b4c9fbdd566b44eba6bf081c705", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/isort-4.2.5-py27_0.tar.bz2"
  }, 
  "itsdangerous-0.24-py27_0": {
    "md5": "989badfae3176772329ad7a4f25de811", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/itsdangerous-0.24-py27_0.tar.bz2"
  }, 
  "jbig-2.1-0": {
    "md5": "2046c46e24fdb82c832e3fd4a25cd0cc", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jbig-2.1-0.tar.bz2"
  }, 
  "jdcal-1.3-py27_0": {
    "md5": "787162123c1afc516441b1f06b50db2b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jdcal-1.3-py27_0.tar.bz2"
  }, 
  "jinja2-2.9.6-py27_0": {
    "md5": "58c087fcd2cacf180c3187475b964f66", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jinja2-2.9.6-py27_0.tar.bz2"
  }, 
  "jpeg-9b-0": {
    "md5": "d868081fe91236ce18aff49e62259807", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jpeg-9b-0.tar.bz2"
  }, 
  "jsonschema-2.6.0-py27_0": {
    "md5": "97512d749d52edefc38c36e9c8e199a2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jsonschema-2.6.0-py27_0.tar.bz2"
  }, 
  "jupyter-1.0.0-py27_3": {
    "md5": "af8a86da2ece79b706238620f6ebeb99", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jupyter-1.0.0-py27_3.tar.bz2"
  }, 
  "jupyter_client-5.0.1-py27_0": {
    "md5": "ce57f0ded58de5b828f149f63305065a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jupyter_client-5.0.1-py27_0.tar.bz2"
  }, 
  "jupyter_console-5.1.0-py27_0": {
    "md5": "61bdd063623f9b77829ff74f33d8199a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jupyter_console-5.1.0-py27_0.tar.bz2"
  }, 
  "jupyter_core-4.3.0-py27_0": {
    "md5": "6ca504498c857e689337c3e4b326fbec", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/jupyter_core-4.3.0-py27_0.tar.bz2"
  }, 
  "lazy-object-proxy-1.2.2-py27_0": {
    "md5": "0ce114670aa7af784ec37ae94235ad93", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/lazy-object-proxy-1.2.2-py27_0.tar.bz2"
  }, 
  "libffi-3.2.1-1": {
    "md5": "68a782271db08963c96e98cc42763da3", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libffi-3.2.1-1.tar.bz2"
  }, 
  "libiconv-1.14-0": {
    "md5": "b21c41b99553f0b147f15b31bd76e17c", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libiconv-1.14-0.tar.bz2"
  }, 
  "libpng-1.6.27-0": {
    "md5": "41dd276798191787af6d95ec3f6c54e7", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libpng-1.6.27-0.tar.bz2"
  }, 
  "libsodium-1.0.10-0": {
    "md5": "6d10205172f14f31eb66c1fb0dba38ca", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libsodium-1.0.10-0.tar.bz2"
  }, 
  "libtiff-4.0.6-3": {
    "md5": "89dca94c43634023badcbc171da72e0d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libtiff-4.0.6-3.tar.bz2"
  }, 
  "libxml2-2.9.4-0": {
    "md5": "8db63173d50e42e2512504c6c6d72e9d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libxml2-2.9.4-0.tar.bz2"
  }, 
  "libxslt-1.1.29-0": {
    "md5": "4a30b8e7949881f9861746aeb63d8cad", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/libxslt-1.1.29-0.tar.bz2"
  }, 
  "locket-0.2.0-py27_1": {
    "md5": "e5824ce1d82a6e8c1e76d000153dd8c5", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/locket-0.2.0-py27_1.tar.bz2"
  }, 
  "lxml-3.7.3-py27_0": {
    "md5": "173cf98b5f5a995668d0e239a82260d6", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/lxml-3.7.3-py27_0.tar.bz2"
  }, 
  "markupsafe-0.23-py27_2": {
    "md5": "5e38b7467bfa7abdb745d87e38be8b85", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/markupsafe-0.23-py27_2.tar.bz2"
  }, 
  "matplotlib-2.0.2-np112py27_0": {
    "md5": "61cb7f5ad5e1d8a21b0234d8632f7620", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/matplotlib-2.0.2-np112py27_0.tar.bz2"
  }, 
  "mistune-0.7.4-py27_0": {
    "md5": "e5990ccb223983279f5d4ee6b6b708d6", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/mistune-0.7.4-py27_0.tar.bz2"
  }, 
  "mpmath-0.19-py27_1": {
    "md5": "9bf91cdada29b95eec477c3b4984ce83", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/mpmath-0.19-py27_1.tar.bz2"
  }, 
  "msgpack-python-0.4.8-py27_0": {
    "md5": "b141ee15bc7d0fbf1ce41eaa6354770f", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/msgpack-python-0.4.8-py27_0.tar.bz2"
  }, 
  "multipledispatch-0.4.9-py27_0": {
    "md5": "aa4ee89b4278b3643a64109d1fece5af", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/multipledispatch-0.4.9-py27_0.tar.bz2"
  }, 
  "nbconvert-5.1.1-py27_0": {
    "md5": "027a378761b65b9b533ee42de6d09c6e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/nbconvert-5.1.1-py27_0.tar.bz2"
  }, 
  "nbformat-4.3.0-py27_0": {
    "md5": "913acbe766ed6bcc1dd21e1f92ca9a01", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/nbformat-4.3.0-py27_0.tar.bz2"
  }, 
  "networkx-1.11-py27_0": {
    "md5": "8a6e90ed40ad43d246bd4a01f3746c34", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/networkx-1.11-py27_0.tar.bz2"
  }, 
  "nltk-3.2.2-py27_0": {
    "md5": "6ba76a78ed191f4b9e479dcdc91a1b53", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/nltk-3.2.2-py27_0.tar.bz2"
  }, 
  "nose-1.3.7-py27_1": {
    "md5": "548df2c53a8075ee150b19d2a1c24de4", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/nose-1.3.7-py27_1.tar.bz2"
  }, 
  "notebook-5.0.0-py27_0": {
    "md5": "596d9e5ebf92799e2549c9d5b440f033", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/notebook-5.0.0-py27_0.tar.bz2"
  }, 
  "numexpr-2.6.2-np112py27_0": {
    "md5": "3063ae9ed0011377cc4ee33308239e95", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/numexpr-2.6.2-np112py27_0.tar.bz2"
  }, 
  "numpy-1.12.1-py27_0": {
    "md5": "54327bf053f3c8ea65e53c931b19985b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/numpy-1.12.1-py27_0.tar.bz2"
  }, 
  "numpydoc-0.6.0-py27_0": {
    "md5": "e94e1f0ad535a11c1375e883e56de2df", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/numpydoc-0.6.0-py27_0.tar.bz2"
  }, 
  "odo-0.5.0-py27_1": {
    "md5": "3f166966e029c9425e4f55d104d899d7", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/odo-0.5.0-py27_1.tar.bz2"
  }, 
  "olefile-0.44-py27_0": {
    "md5": "9de9b945c5a1065ddb214fdbe685c689", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/olefile-0.44-py27_0.tar.bz2"
  }, 
  "openblas-0.2.19-0": {
    "md5": "9c07979a0188bf576bc161a4802d91ea", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/openblas-0.2.19-0.tar.bz2"
  }, 
  "openpyxl-2.4.7-py27_0": {
    "md5": "8a8074498a4f5155b72ff1b72542bdbf", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/openpyxl-2.4.7-py27_0.tar.bz2"
  }, 
  "openssl-1.0.2k-2": {
    "md5": "af0f9df1cd31a0027eb27cd36d940933", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/openssl-1.0.2k-2.tar.bz2"
  }, 
  "packaging-16.8-py27_0": {
    "md5": "eeed47d3c6fdce7cb1de4a98430e360b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/packaging-16.8-py27_0.tar.bz2"
  }, 
  "pandas-0.20.1-np112py27_0": {
    "md5": "0830d527635160978ecbc2bd543ec4c5", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pandas-0.20.1-np112py27_0.tar.bz2"
  }, 
  "pandocfilters-1.4.1-py27_0": {
    "md5": "b8dcec65b128f6071c002da2be537735", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pandocfilters-1.4.1-py27_0.tar.bz2"
  }, 
  "partd-0.3.8-py27_0": {
    "md5": "4074bc43e5d6abb7c16aaedfa4703713", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/partd-0.3.8-py27_0.tar.bz2"
  }, 
  "path.py-10.3.1-py27_0": {
    "md5": "4295a410939979170f7ebc64729afdb7", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/path.py-10.3.1-py27_0.tar.bz2"
  }, 
  "pathlib2-2.2.1-py27_0": {
    "md5": "98e78f2cb0b24768c4e43e9e954a4703", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pathlib2-2.2.1-py27_0.tar.bz2"
  }, 
  "patsy-0.4.1-py27_0": {
    "md5": "52bb9cb16e8d2e97f5f4db63097d1257", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/patsy-0.4.1-py27_0.tar.bz2"
  }, 
  "pcre-8.39-1": {
    "md5": "2c79dc398e564c65d3708fe4911732a4", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pcre-8.39-1.tar.bz2"
  }, 
  "pep8-1.7.0-py27_0": {
    "md5": "70ccab04b4b20952883c65e910e6b2ce", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pep8-1.7.0-py27_0.tar.bz2"
  }, 
  "pexpect-4.2.1-py27_0": {
    "md5": "7830920856409915297873e2858515ed", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pexpect-4.2.1-py27_0.tar.bz2"
  }, 
  "pickleshare-0.7.4-py27_0": {
    "md5": "14388ccdbfe22d4b1b4d8ed2fe076d16", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pickleshare-0.7.4-py27_0.tar.bz2"
  }, 
  "pillow-4.1.1-py27_0": {
    "md5": "ba2770d7b73eb6104febe5346d126be2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pillow-4.1.1-py27_0.tar.bz2"
  }, 
  "pip-9.0.1-py27_1": {
    "md5": "bafb95bcca3f848d452478a3a00a2b0a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pip-9.0.1-py27_1.tar.bz2"
  }, 
  "pixman-0.34.0-0": {
    "md5": "1d827627c1ac8c956fd5addbeccbdbd1", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pixman-0.34.0-0.tar.bz2"
  }, 
  "ply-3.10-py27_0": {
    "md5": "2026372106b4faace6c6eab5ef7c0405", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ply-3.10-py27_0.tar.bz2"
  }, 
  "prompt_toolkit-1.0.14-py27_0": {
    "md5": "d0ce51a6db4767bd17b72a6e2d094ddb", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/prompt_toolkit-1.0.14-py27_0.tar.bz2"
  }, 
  "psutil-5.2.2-py27_0": {
    "md5": "3526748b43a47cee45c8bff5c005bb10", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/psutil-5.2.2-py27_0.tar.bz2"
  }, 
  "ptyprocess-0.5.1-py27_0": {
    "md5": "a98a8d7b3abae315a25841e9390d4ceb", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ptyprocess-0.5.1-py27_0.tar.bz2"
  }, 
  "py-1.4.33-py27_0": {
    "md5": "6d646fba32175991cae5833ba8c4f941", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/py-1.4.33-py27_0.tar.bz2"
  }, 
  "pycairo-1.10.0-py27_0": {
    "md5": "8aeb555d72797b1d9a599512e3551c3d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pycairo-1.10.0-py27_0.tar.bz2"
  }, 
  "pycosat-0.6.2-py27_0": {
    "md5": "a6af9d31d7ad7a61fc819d8a476e9549", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pycosat-0.6.2-py27_0.tar.bz2"
  }, 
  "pycparser-2.17-py27_0": {
    "md5": "aa9332ab606365964ed4dbc628f4cc9d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pycparser-2.17-py27_0.tar.bz2"
  }, 
  "pycrypto-2.6.1-py27_4": {
    "md5": "c7543d8d57d19d871696adc29c59b4b1", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pycrypto-2.6.1-py27_4.tar.bz2"
  }, 
  "pycurl-7.43.0-py27_2": {
    "md5": "7f419f7741a3d3fe71df89141625e364", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pycurl-7.43.0-py27_2.tar.bz2"
  }, 
  "pyflakes-1.5.0-py27_0": {
    "md5": "a38e4032fc300c1159150df58463d7f3", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyflakes-1.5.0-py27_0.tar.bz2"
  }, 
  "pygments-2.2.0-py27_0": {
    "md5": "eaac917618b754ca4e3356c1409875ae", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pygments-2.2.0-py27_0.tar.bz2"
  }, 
  "pylint-1.6.4-py27_1": {
    "md5": "a84251990e8d2ef37d9e5ba58226dd81", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pylint-1.6.4-py27_1.tar.bz2"
  }, 
  "pyodbc-4.0.16-py27_0": {
    "md5": "e4bb9eb984f18c26a4e6ce164fc07e9e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyodbc-4.0.16-py27_0.tar.bz2"
  }, 
  "pyopenssl-17.0.0-py27_0": {
    "md5": "85b4015d472f423cdca4143e6106ec81", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyopenssl-17.0.0-py27_0.tar.bz2"
  }, 
  "pyparsing-2.1.4-py27_0": {
    "md5": "a3137070c6f32f6571c1c34c90f5cc96", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyparsing-2.1.4-py27_0.tar.bz2"
  }, 
  "pytables-3.2.2-np112py27_4": {
    "md5": "133b5d24eb1aa1f0397d6972ea286ad6", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pytables-3.2.2-np112py27_4.tar.bz2"
  }, 
  "pytest-3.0.7-py27_0": {
    "md5": "ce51705bff558e59ac079c5ee2c2ad49", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pytest-3.0.7-py27_0.tar.bz2"
  }, 
  "python-2.7.13-0": {
    "md5": "0f4db1a63e9134b429e4eae7a6a9a35f", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/python-2.7.13-0.tar.bz2"
  }, 
  "python-dateutil-2.6.0-py27_0": {
    "md5": "f5a64a37647cda2db167a110eea7b52d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/python-dateutil-2.6.0-py27_0.tar.bz2"
  }, 
  "pytz-2017.2-py27_0": {
    "md5": "bdf6a66fa05541008fa2305a51ddbc7e", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pytz-2017.2-py27_0.tar.bz2"
  }, 
  "pywavelets-0.5.2-np112py27_0": {
    "md5": "594724e6d9da1e518613e74456ea3ee9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pywavelets-0.5.2-np112py27_0.tar.bz2"
  }, 
  "pyyaml-3.12-py27_0": {
    "md5": "74d18e1dcaac6f717e798d34e46dc43b", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyyaml-3.12-py27_0.tar.bz2"
  }, 
  "pyzmq-16.0.2-py27_0": {
    "md5": "22957260da9fb0c39fb4e47b41bffa91", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/pyzmq-16.0.2-py27_0.tar.bz2"
  }, 
  "redis-3.2.0-0": {
    "md5": "5dfd80b7ef8639a0742f41270c1f86dc", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/redis-3.2.0-0.tar.bz2"
  }, 
  "redis-py-2.10.5-py27_0": {
    "md5": "d2f9fba80670763b11d6ae0ab6604b7a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/redis-py-2.10.5-py27_0.tar.bz2"
  }, 
  "requests-2.14.2-py27_0": {
    "md5": "3eb3bc50b1deb232456af5cacda0b4f9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/requests-2.14.2-py27_0.tar.bz2"
  }, 
  "ruamel_yaml-0.11.14-py27_1": {
    "md5": "7a4b465d17e2e2e474b8bd03114d70cb", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ruamel_yaml-0.11.14-py27_1.tar.bz2"
  }, 
  "scandir-1.5-py27_0": {
    "md5": "2111fd5c7e0e5dbc8833e5b2ce794560", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/scandir-1.5-py27_0.tar.bz2"
  }, 
  "scikit-image-0.13.0-np112py27_0": {
    "md5": "f526729850d22b180eb0c4c096773ed4", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/scikit-image-0.13.0-np112py27_0.tar.bz2"
  }, 
  "scikit-learn-0.18.1-np112py27_1": {
    "md5": "f46a42b67c97d229ed82f3a5d65c4ce3", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/scikit-learn-0.18.1-np112py27_1.tar.bz2"
  }, 
  "scipy-0.19.0-np112py27_0": {
    "md5": "5a54c61ea21fedea953c31ef0bd44737", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/scipy-0.19.0-np112py27_0.tar.bz2"
  }, 
  "seaborn-0.7.1-py27_0": {
    "md5": "3b49b4e2a5f5c668a5c44fb66efe7f64", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/seaborn-0.7.1-py27_0.tar.bz2"
  }, 
  "setuptools-27.2.0-py27_0": {
    "md5": "b439c98dbed13e6d3f6ae423427c0667", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/setuptools-27.2.0-py27_0.tar.bz2"
  }, 
  "simplegeneric-0.8.1-py27_1": {
    "md5": "c6d6789c12040ebcd91c3546129ae993", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/simplegeneric-0.8.1-py27_1.tar.bz2"
  }, 
  "singledispatch-3.4.0.3-py27_0": {
    "md5": "5a6bbc81350c21b639116a78e777ab5a", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/singledispatch-3.4.0.3-py27_0.tar.bz2"
  }, 
  "six-1.10.0-py27_0": {
    "md5": "f442e642312f51f56e2b070fbdc498c5", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/six-1.10.0-py27_0.tar.bz2"
  }, 
  "snowballstemmer-1.2.1-py27_0": {
    "md5": "3797ec7b3f5a21b2127f300207985041", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/snowballstemmer-1.2.1-py27_0.tar.bz2"
  }, 
  "sockjs-tornado-1.0.3-py27_0": {
    "md5": "94b453ae95b1529fc05aacc5501b49e9", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sockjs-tornado-1.0.3-py27_0.tar.bz2"
  }, 
  "sortedcollections-0.5.3-py27_0": {
    "md5": "c70d614d8f7976be407875319f4e992c", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sortedcollections-0.5.3-py27_0.tar.bz2"
  }, 
  "sortedcontainers-1.5.7-py27_0": {
    "md5": "92b018f049b66c0a0ea44bdb032d23f1", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sortedcontainers-1.5.7-py27_0.tar.bz2"
  }, 
  "sphinx-1.5.6-py27_0": {
    "md5": "c0c11c283b880419b680f2b46ae3ed03", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sphinx-1.5.6-py27_0.tar.bz2"
  }, 
  "sqlalchemy-1.1.9-py27_0": {
    "md5": "8bced5d2006c723fea37282ec0900a1d", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sqlalchemy-1.1.9-py27_0.tar.bz2"
  }, 
  "sqlite-3.13.0-0": {
    "md5": "da58ff3644b5d03d1a62451c4357112c", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sqlite-3.13.0-0.tar.bz2"
  }, 
  "ssl_match_hostname-3.4.0.2-py27_1": {
    "md5": "b5fceeeb75d57a614da307d42b9bbb08", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/ssl_match_hostname-3.4.0.2-py27_1.tar.bz2"
  }, 
  "statsmodels-0.8.0-np112py27_0": {
    "md5": "20805a72dcdb077045820db107c0a047", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/statsmodels-0.8.0-np112py27_0.tar.bz2"
  }, 
  "subprocess32-3.2.7-py27_0": {
    "md5": "dea9a66853f542c7f05669dd68bc2482", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/subprocess32-3.2.7-py27_0.tar.bz2"
  }, 
  "sympy-1.0-py27_0": {
    "md5": "43bf044f3a7eddb6f7b0f9b1b03376eb", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/sympy-1.0-py27_0.tar.bz2"
  }, 
  "tblib-1.3.2-py27_0": {
    "md5": "4c8634238cb5fa9dd8be157485a98e72", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/tblib-1.3.2-py27_0.tar.bz2"
  }, 
  "terminado-0.6-py27_0": {
    "md5": "39621140666395b6dc348c1f184714d5", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/terminado-0.6-py27_0.tar.bz2"
  }, 
  "testpath-0.3-py27_0": {
    "md5": "cb79ef177d55673b01ee665ca98fc0ea", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/testpath-0.3-py27_0.tar.bz2"
  }, 
  "tk-8.5.18-0": {
    "md5": "9ec5c8dfa44797b1c176237d1bbf8369", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/tk-8.5.18-0.tar.bz2"
  }, 
  "toolz-0.8.2-py27_0": {
    "md5": "a8d7ed8417abb5a98f6d77fb2feee981", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/toolz-0.8.2-py27_0.tar.bz2"
  }, 
  "tornado-4.5.1-py27_0": {
    "md5": "9fd71f07564a8c3400275ac0cd3e1ace", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/tornado-4.5.1-py27_0.tar.bz2"
  }, 
  "traitlets-4.3.2-py27_0": {
    "md5": "8f1c8c1152f5741b39482cb9da7bbba2", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/traitlets-4.3.2-py27_0.tar.bz2"
  }, 
  "unicodecsv-0.14.1-py27_0": {
    "md5": "c6e8690c2ee1649293f69a50ac8deea1", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/unicodecsv-0.14.1-py27_0.tar.bz2"
  }, 
  "unixodbc-2.3.4-0": {
    "md5": "fb1894a027dc1a30ed509a0b1c05f5c5", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/unixodbc-2.3.4-0.tar.bz2"
  }, 
  "wcwidth-0.1.7-py27_0": {
    "md5": "4d7970bae692da004cc498941b600dda", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/wcwidth-0.1.7-py27_0.tar.bz2"
  }, 
  "werkzeug-0.12.2-py27_0": {
    "md5": "023efeee1388fcb5bb206c1138d759e0", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/werkzeug-0.12.2-py27_0.tar.bz2"
  }, 
  "wheel-0.29.0-py27_0": {
    "md5": "5348e62853f97599a9fab61f93f7c6ee", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/wheel-0.29.0-py27_0.tar.bz2"
  }, 
  "widgetsnbextension-2.0.0-py27_0": {
    "md5": "36d1edf2bcb4ccdc5cf03955c8f5e5ea", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/widgetsnbextension-2.0.0-py27_0.tar.bz2"
  }, 
  "wrapt-1.10.10-py27_0": {
    "md5": "4e3a8529f7d3d0f338644bf58ad570ec", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/wrapt-1.10.10-py27_0.tar.bz2"
  }, 
  "xlrd-1.0.0-py27_0": {
    "md5": "2db68c76ac6a746fdbd20e1e55e86f49", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/xlrd-1.0.0-py27_0.tar.bz2"
  }, 
  "xlsxwriter-0.9.6-py27_0": {
    "md5": "46aa00ef4eba98baf1d85e676832b6df", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/xlsxwriter-0.9.6-py27_0.tar.bz2"
  }, 
  "xlwt-1.2.0-py27_0": {
    "md5": "f82da56f2e446c05a29753850740a672", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/xlwt-1.2.0-py27_0.tar.bz2"
  }, 
  "xz-5.2.2-1": {
    "md5": "d37850b6dc2cd4e05daf5ed2245f9849", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/xz-5.2.2-1.tar.bz2"
  }, 
  "yaml-0.1.6-0": {
    "md5": "41fa95d987dd40f208a726761c23df06", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/yaml-0.1.6-0.tar.bz2"
  }, 
  "zeromq-4.1.5-0": {
    "md5": "ab721ed581400da9b7ad3fb5813bb143", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/zeromq-4.1.5-0.tar.bz2"
  }, 
  "zict-0.1.2-py27_0": {
    "md5": "2ca679e37911b641ee60916e273ad7b1", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/zict-0.1.2-py27_0.tar.bz2"
  }, 
  "zlib-1.2.8-3": {
    "md5": "ac44280eb1998f323c7cd40f19195142", 
    "url": "https://repo.continuum.io/pkgs/free/linux-ppc64le/zlib-1.2.8-3.tar.bz2"
  }
}
C_ENVS = {
  "root": [
    "python-2.7.13-0", 
    "alabaster-0.7.10-py27_0", 
    "anaconda-client-1.6.3-py27_0", 
    "anaconda-project-0.4.1-py27_0", 
    "asn1crypto-0.22.0-py27_0", 
    "astroid-1.4.9-py27_0", 
    "astropy-1.3.2-np112py27_0", 
    "babel-2.4.0-py27_0", 
    "backports-1.0-py27_0", 
    "backports_abc-0.5-py27_0", 
    "beautifulsoup4-4.6.0-py27_0", 
    "bitarray-0.8.1-py27_0", 
    "bleach-1.5.0-py27_0", 
    "bokeh-0.12.5-py27_0", 
    "boto-2.46.1-py27_0", 
    "bottleneck-1.2.1-np112py27_0", 
    "cairo-1.14.8-0", 
    "cdecimal-2.3-py27_2", 
    "cffi-1.10.0-py27_0", 
    "chardet-3.0.3-py27_0", 
    "chest-0.2.3-py27_0", 
    "click-6.7-py27_0", 
    "cloudpickle-0.2.2-py27_0", 
    "clyent-1.2.2-py27_0", 
    "colorama-0.3.9-py27_0", 
    "configobj-5.0.6-py27_0", 
    "configparser-3.5.0-py27_0", 
    "contextlib2-0.5.5-py27_0", 
    "cryptography-1.8.1-py27_0", 
    "curl-7.52.1-0", 
    "cycler-0.10.0-py27_0", 
    "cython-0.25.2-py27_0", 
    "cytoolz-0.8.2-py27_0", 
    "dask-0.14.3-py27_0", 
    "datashape-0.5.4-py27_0", 
    "decorator-4.0.11-py27_0", 
    "distributed-1.16.3-py27_0", 
    "docutils-0.13.1-py27_0", 
    "entrypoints-0.2.2-py27_1", 
    "enum34-1.1.6-py27_0", 
    "et_xmlfile-1.0.1-py27_0", 
    "expat-2.1.0-0", 
    "fastcache-1.0.2-py27_1", 
    "flask-0.12.2-py27_0", 
    "flask-cors-3.0.2-py27_0", 
    "fontconfig-2.12.1-3", 
    "freetype-2.5.5-2", 
    "funcsigs-1.0.2-py27_0", 
    "functools32-3.2.3.2-py27_0", 
    "futures-3.1.1-py27_0", 
    "get_terminal_size-1.0.0-py27_0", 
    "gevent-1.2.1-py27_0", 
    "greenlet-0.4.12-py27_0", 
    "grin-1.2.1-py27_3", 
    "h5py-2.7.0-np112py27_0", 
    "hdf5-1.8.17-1", 
    "heapdict-1.0.0-py27_1", 
    "html5lib-0.999-py27_0", 
    "idna-2.5-py27_0", 
    "imagesize-0.7.1-py27_0", 
    "ipaddress-1.0.18-py27_0", 
    "ipykernel-4.6.1-py27_0", 
    "ipython-5.3.0-py27_0", 
    "ipython_genutils-0.2.0-py27_0", 
    "ipywidgets-6.0.0-py27_0", 
    "isort-4.2.5-py27_0", 
    "itsdangerous-0.24-py27_0", 
    "jbig-2.1-0", 
    "jdcal-1.3-py27_0", 
    "jinja2-2.9.6-py27_0", 
    "jpeg-9b-0", 
    "jsonschema-2.6.0-py27_0", 
    "jupyter-1.0.0-py27_3", 
    "jupyter_client-5.0.1-py27_0", 
    "jupyter_console-5.1.0-py27_0", 
    "jupyter_core-4.3.0-py27_0", 
    "lazy-object-proxy-1.2.2-py27_0", 
    "libffi-3.2.1-1", 
    "libiconv-1.14-0", 
    "libpng-1.6.27-0", 
    "libsodium-1.0.10-0", 
    "libtiff-4.0.6-3", 
    "libxml2-2.9.4-0", 
    "libxslt-1.1.29-0", 
    "locket-0.2.0-py27_1", 
    "lxml-3.7.3-py27_0", 
    "markupsafe-0.23-py27_2", 
    "matplotlib-2.0.2-np112py27_0", 
    "mistune-0.7.4-py27_0", 
    "mpmath-0.19-py27_1", 
    "msgpack-python-0.4.8-py27_0", 
    "multipledispatch-0.4.9-py27_0", 
    "nbconvert-5.1.1-py27_0", 
    "nbformat-4.3.0-py27_0", 
    "networkx-1.11-py27_0", 
    "nltk-3.2.2-py27_0", 
    "nose-1.3.7-py27_1", 
    "notebook-5.0.0-py27_0", 
    "numexpr-2.6.2-np112py27_0", 
    "numpy-1.12.1-py27_0", 
    "numpydoc-0.6.0-py27_0", 
    "odo-0.5.0-py27_1", 
    "olefile-0.44-py27_0", 
    "openblas-0.2.19-0", 
    "openpyxl-2.4.7-py27_0", 
    "openssl-1.0.2k-2", 
    "packaging-16.8-py27_0", 
    "pandas-0.20.1-np112py27_0", 
    "pandocfilters-1.4.1-py27_0", 
    "partd-0.3.8-py27_0", 
    "path.py-10.3.1-py27_0", 
    "pathlib2-2.2.1-py27_0", 
    "patsy-0.4.1-py27_0", 
    "pcre-8.39-1", 
    "pep8-1.7.0-py27_0", 
    "pexpect-4.2.1-py27_0", 
    "pickleshare-0.7.4-py27_0", 
    "pillow-4.1.1-py27_0", 
    "pip-9.0.1-py27_1", 
    "pixman-0.34.0-0", 
    "ply-3.10-py27_0", 
    "prompt_toolkit-1.0.14-py27_0", 
    "psutil-5.2.2-py27_0", 
    "ptyprocess-0.5.1-py27_0", 
    "py-1.4.33-py27_0", 
    "pycairo-1.10.0-py27_0", 
    "pycosat-0.6.2-py27_0", 
    "pycparser-2.17-py27_0", 
    "pycrypto-2.6.1-py27_4", 
    "pycurl-7.43.0-py27_2", 
    "pyflakes-1.5.0-py27_0", 
    "pygments-2.2.0-py27_0", 
    "pylint-1.6.4-py27_1", 
    "pyodbc-4.0.16-py27_0", 
    "pyopenssl-17.0.0-py27_0", 
    "pyparsing-2.1.4-py27_0", 
    "pytables-3.2.2-np112py27_4", 
    "pytest-3.0.7-py27_0", 
    "python-dateutil-2.6.0-py27_0", 
    "pytz-2017.2-py27_0", 
    "pywavelets-0.5.2-np112py27_0", 
    "pyyaml-3.12-py27_0", 
    "pyzmq-16.0.2-py27_0", 
    "redis-3.2.0-0", 
    "redis-py-2.10.5-py27_0", 
    "requests-2.14.2-py27_0", 
    "ruamel_yaml-0.11.14-py27_1", 
    "scandir-1.5-py27_0", 
    "scikit-image-0.13.0-np112py27_0", 
    "scikit-learn-0.18.1-np112py27_1", 
    "scipy-0.19.0-np112py27_0", 
    "seaborn-0.7.1-py27_0", 
    "setuptools-27.2.0-py27_0", 
    "simplegeneric-0.8.1-py27_1", 
    "singledispatch-3.4.0.3-py27_0", 
    "six-1.10.0-py27_0", 
    "snowballstemmer-1.2.1-py27_0", 
    "sockjs-tornado-1.0.3-py27_0", 
    "sortedcollections-0.5.3-py27_0", 
    "sortedcontainers-1.5.7-py27_0", 
    "sphinx-1.5.6-py27_0", 
    "sqlalchemy-1.1.9-py27_0", 
    "sqlite-3.13.0-0", 
    "ssl_match_hostname-3.4.0.2-py27_1", 
    "statsmodels-0.8.0-np112py27_0", 
    "subprocess32-3.2.7-py27_0", 
    "sympy-1.0-py27_0", 
    "tblib-1.3.2-py27_0", 
    "terminado-0.6-py27_0", 
    "testpath-0.3-py27_0", 
    "tk-8.5.18-0", 
    "toolz-0.8.2-py27_0", 
    "tornado-4.5.1-py27_0", 
    "traitlets-4.3.2-py27_0", 
    "unicodecsv-0.14.1-py27_0", 
    "unixodbc-2.3.4-0", 
    "wcwidth-0.1.7-py27_0", 
    "werkzeug-0.12.2-py27_0", 
    "wheel-0.29.0-py27_0", 
    "widgetsnbextension-2.0.0-py27_0", 
    "wrapt-1.10.10-py27_0", 
    "xlrd-1.0.0-py27_0", 
    "xlsxwriter-0.9.6-py27_0", 
    "xlwt-1.2.0-py27_0", 
    "xz-5.2.2-1", 
    "yaml-0.1.6-0", 
    "zeromq-4.1.5-0", 
    "zict-0.1.2-py27_0", 
    "zlib-1.2.8-3", 
    "anaconda-4.4.0-np112py27_0", 
    "conda-4.3.18-py27_0", 
    "conda-env-2.6.0-0"
  ]
}



def _link(src, dst, linktype=LINK_HARD):
    if on_win:
        raise NotImplementedError

    if linktype == LINK_HARD:
        os.link(src, dst)
    elif linktype == LINK_COPY:
        # copy relative symlinks as symlinks
        if islink(src) and not os.readlink(src).startswith('/'):
            os.symlink(os.readlink(src), dst)
        else:
            shutil.copy2(src, dst)
    else:
        raise Exception("Did not expect linktype=%r" % linktype)


def rm_rf(path):
    """
    try to delete path, but never fail
    """
    try:
        if islink(path) or isfile(path):
            # Note that we have to check if the destination is a link because
            # exists('/path/to/dead-link') will return False, although
            # islink('/path/to/dead-link') is True.
            os.unlink(path)
        elif isdir(path):
            shutil.rmtree(path)
    except (OSError, IOError):
        pass


def yield_lines(path):
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        yield line


prefix_placeholder = ('/opt/anaconda1anaconda2'
                      # this is intentionally split into parts,
                      # such that running this program on itself
                      # will leave it unchanged
                      'anaconda3')

def read_has_prefix(path):
    """
    reads `has_prefix` file and return dict mapping filenames to
    tuples(placeholder, mode)
    """
    import shlex

    res = {}
    try:
        for line in yield_lines(path):
            try:
                placeholder, mode, f = [x.strip('"\'') for x in
                                        shlex.split(line, posix=False)]
                res[f] = (placeholder, mode)
            except ValueError:
                res[line] = (prefix_placeholder, 'text')
    except IOError:
        pass
    return res


def exp_backoff_fn(fn, *args):
    """
    for retrying file operations that fail on Windows due to virus scanners
    """
    if not on_win:
        return fn(*args)

    import time
    import errno
    max_tries = 6  # max total time = 6.4 sec
    for n in range(max_tries):
        try:
            result = fn(*args)
        except (OSError, IOError) as e:
            if e.errno in (errno.EPERM, errno.EACCES):
                if n == max_tries - 1:
                    raise Exception("max_tries=%d reached" % max_tries)
                time.sleep(0.1 * (2 ** n))
            else:
                raise e
        else:
            return result


class PaddingError(Exception):
    pass


def binary_replace(data, a, b):
    """
    Perform a binary replacement of `data`, where the placeholder `a` is
    replaced with `b` and the remaining string is padded with null characters.
    All input arguments are expected to be bytes objects.
    """
    def replace(match):
        occurances = match.group().count(a)
        padding = (len(a) - len(b)) * occurances
        if padding < 0:
            raise PaddingError(a, b, padding)
        return match.group().replace(a, b) + b'\0' * padding

    pat = re.compile(re.escape(a) + b'([^\0]*?)\0')
    res = pat.sub(replace, data)
    assert len(res) == len(data)
    return res


def update_prefix(path, new_prefix, placeholder, mode):
    if on_win:
        # force all prefix replacements to forward slashes to simplify need
        # to escape backslashes - replace with unix-style path separators
        new_prefix = new_prefix.replace('\\', '/')

    path = os.path.realpath(path)
    with open(path, 'rb') as fi:
        data = fi.read()
    if mode == 'text':
        new_data = data.replace(placeholder.encode('utf-8'),
                                new_prefix.encode('utf-8'))
    elif mode == 'binary':
        if on_win:
            # anaconda-verify will not allow binary placeholder on Windows.
            # However, since some packages might be created wrong (and a
            # binary placeholder would break the package, we just skip here.
            return
        new_data = binary_replace(data, placeholder.encode('utf-8'),
                                  new_prefix.encode('utf-8'))
    else:
        sys.exit("Invalid mode:" % mode)

    if new_data == data:
        return
    st = os.lstat(path)
    # unlink in case the file is memory mapped
    exp_backoff_fn(os.unlink, path)
    with open(path, 'wb') as fo:
        fo.write(new_data)
    os.chmod(path, stat.S_IMODE(st.st_mode))


def name_dist(dist):
    return dist.rsplit('-', 2)[0]


def create_meta(prefix, dist, info_dir, extra_info):
    """
    Create the conda metadata, in a given prefix, for a given package.
    """
    # read info/index.json first
    with open(join(info_dir, 'index.json')) as fi:
        meta = json.load(fi)
    # add extra info
    meta.update(extra_info)
    # write into <prefix>/conda-meta/<dist>.json
    meta_dir = join(prefix, 'conda-meta')
    if not isdir(meta_dir):
        os.makedirs(meta_dir)
        with open(join(meta_dir, 'history'), 'w') as fo:
            fo.write('')
    with open(join(meta_dir, dist + '.json'), 'w') as fo:
        json.dump(meta, fo, indent=2, sort_keys=True)


def run_script(prefix, dist, action='post-link'):
    """
    call the post-link (or pre-unlink) script, and return True on success,
    False on failure
    """
    path = join(prefix, 'Scripts' if on_win else 'bin', '.%s-%s.%s' % (
            name_dist(dist),
            action,
            'bat' if on_win else 'sh'))
    if not isfile(path):
        return True
    if SKIP_SCRIPTS:
        print("WARNING: skipping %s script by user request" % action)
        return True

    if on_win:
        try:
            args = [os.environ['COMSPEC'], '/c', path]
        except KeyError:
            return False
    else:
        shell_path = '/bin/sh' if 'bsd' in sys.platform else '/bin/bash'
        args = [shell_path, path]

    env = os.environ
    env['PREFIX'] = prefix

    import subprocess
    try:
        subprocess.check_call(args, env=env)
    except subprocess.CalledProcessError:
        return False
    return True


url_pat = re.compile(r'''
(?P<baseurl>\S+/)                 # base URL
(?P<fn>[^\s#/]+)                  # filename
([#](?P<md5>[0-9a-f]{32}))?       # optional MD5
$                                 # EOL
''', re.VERBOSE)

def read_urls(dist):
    try:
        data = open(join(PKGS_DIR, 'urls')).read()
        for line in data.split()[::-1]:
            m = url_pat.match(line)
            if m is None:
                continue
            if m.group('fn') == '%s.tar.bz2' % dist:
                return {'url': m.group('baseurl') + m.group('fn'),
                        'md5': m.group('md5')}
    except IOError:
        pass
    return {}


def read_no_link(info_dir):
    res = set()
    for fn in 'no_link', 'no_softlink':
        try:
            res.update(set(yield_lines(join(info_dir, fn))))
        except IOError:
            pass
    return res


def linked(prefix):
    """
    Return the (set of canonical names) of linked packages in prefix.
    """
    meta_dir = join(prefix, 'conda-meta')
    if not isdir(meta_dir):
        return set()
    return set(fn[:-5] for fn in os.listdir(meta_dir) if fn.endswith('.json'))


def link(prefix, dist, linktype=LINK_HARD):
    '''
    Link a package in a specified prefix.  We assume that the packacge has
    been extra_info in either
      - <PKGS_DIR>/dist
      - <ROOT_PREFIX>/ (when the linktype is None)
    '''
    if linktype:
        source_dir = join(PKGS_DIR, dist)
        info_dir = join(source_dir, 'info')
        no_link = read_no_link(info_dir)
    else:
        info_dir = join(prefix, 'info')

    files = list(yield_lines(join(info_dir, 'files')))
    has_prefix_files = read_has_prefix(join(info_dir, 'has_prefix'))

    if linktype:
        for f in files:
            src = join(source_dir, f)
            dst = join(prefix, f)
            dst_dir = dirname(dst)
            if not isdir(dst_dir):
                os.makedirs(dst_dir)
            if exists(dst):
                if FORCE:
                    rm_rf(dst)
                else:
                    raise Exception("dst exists: %r" % dst)
            lt = linktype
            if f in has_prefix_files or f in no_link or islink(src):
                lt = LINK_COPY
            try:
                _link(src, dst, lt)
            except OSError:
                pass

    for f in sorted(has_prefix_files):
        placeholder, mode = has_prefix_files[f]
        try:
            update_prefix(join(prefix, f), prefix, placeholder, mode)
        except PaddingError:
            sys.exit("ERROR: placeholder '%s' too short in: %s\n" %
                     (placeholder, dist))

    if not run_script(prefix, dist, 'post-link'):
        sys.exit("Error: post-link failed for: %s" % dist)

    meta = {
        'files': files,
        'link': ({'source': source_dir,
                  'type': link_name_map.get(linktype)}
                 if linktype else None),
    }
    try:    # add URL and MD5
        meta.update(IDISTS[dist])
    except KeyError:
        meta.update(read_urls(dist))
    meta['installed_by'] = 'Anaconda2-4.4.0-Linux-ppc64le'
    create_meta(prefix, dist, info_dir, meta)


def duplicates_to_remove(linked_dists, keep_dists):
    """
    Returns the (sorted) list of distributions to be removed, such that
    only one distribution (for each name) remains.  `keep_dists` is an
    interable of distributions (which are not allowed to be removed).
    """
    from collections import defaultdict

    keep_dists = set(keep_dists)
    ldists = defaultdict(set) # map names to set of distributions
    for dist in linked_dists:
        name = name_dist(dist)
        ldists[name].add(dist)

    res = set()
    for dists in ldists.values():
        # `dists` is the group of packages with the same name
        if len(dists) == 1:
            # if there is only one package, nothing has to be removed
            continue
        if dists & keep_dists:
            # if the group has packages which are have to be kept, we just
            # take the set of packages which are in group but not in the
            # ones which have to be kept
            res.update(dists - keep_dists)
        else:
            # otherwise, we take lowest (n-1) (sorted) packages
            res.update(sorted(dists)[:-1])
    return sorted(res)


def remove_duplicates():
    idists = []
    for line in open(join(PKGS_DIR, 'urls')):
        m = url_pat.match(line)
        if m:
            fn = m.group('fn')
            idists.append(fn[:-8])

    keep_files = set()
    for dist in idists:
        with open(join(ROOT_PREFIX, 'conda-meta', dist + '.json')) as fi:
            meta = json.load(fi)
        keep_files.update(meta['files'])

    for dist in duplicates_to_remove(linked(ROOT_PREFIX), idists):
        print("unlinking: %s" % dist)
        meta_path = join(ROOT_PREFIX, 'conda-meta', dist + '.json')
        with open(meta_path) as fi:
            meta = json.load(fi)
        for f in meta['files']:
            if f not in keep_files:
                rm_rf(join(ROOT_PREFIX, f))
        rm_rf(meta_path)


def link_idists():
    src = join(PKGS_DIR, 'urls')
    dst = join(ROOT_PREFIX, '.hard-link')
    assert isfile(src), src
    assert not isfile(dst), dst
    try:
        _link(src, dst, LINK_HARD)
        linktype = LINK_HARD
    except OSError:
        linktype = LINK_COPY
    finally:
        rm_rf(dst)

    for env_name in sorted(C_ENVS):
        dists = C_ENVS[env_name]
        assert isinstance(dists, list)
        if len(dists) == 0:
            continue

        prefix = prefix_env(env_name)
        for dist in dists:
            assert dist in IDISTS
            link(prefix, dist, linktype)

        for dist in duplicates_to_remove(linked(prefix), dists):
            meta_path = join(prefix, 'conda-meta', dist + '.json')
            print("WARNING: unlinking: %s" % meta_path)
            try:
                os.rename(meta_path, meta_path + '.bak')
            except OSError:
                rm_rf(meta_path)


def prefix_env(env_name):
    if env_name == 'root':
        return ROOT_PREFIX
    else:
        return join(ROOT_PREFIX, 'envs', env_name)


def post_extract(env_name='root'):
    """
    assuming that the package is extracted in the environment `env_name`,
    this function does everything link() does except the actual linking,
    i.e. update prefix files, run 'post-link', creates the conda metadata,
    and removed the info/ directory afterwards.
    """
    prefix = prefix_env(env_name)
    info_dir = join(prefix, 'info')
    with open(join(info_dir, 'index.json')) as fi:
        meta = json.load(fi)
    dist = '%(name)s-%(version)s-%(build)s' % meta
    if FORCE:
        run_script(prefix, dist, 'pre-unlink')
    link(prefix, dist, linktype=None)
    shutil.rmtree(info_dir)


def main():
    global ROOT_PREFIX, PKGS_DIR

    p = OptionParser(description="conda link tool used by installers")

    p.add_option('--root-prefix',
                 action="store",
                 default=abspath(join(__file__, '..', '..')),
                 help="root prefix (defaults to %default)")

    p.add_option('--post',
                 action="store",
                 help="perform post extract (on a single package), "
                      "in environment NAME",
                 metavar='NAME')

    opts, args = p.parse_args()
    if args:
        p.error('no arguments expected')

    ROOT_PREFIX = opts.root_prefix.replace('//', '/')
    PKGS_DIR = join(ROOT_PREFIX, 'pkgs')

    if opts.post:
        post_extract(opts.post)
        return

    if FORCE:
        print("using -f (force) option")

    link_idists()


def main2():
    global SKIP_SCRIPTS

    p = OptionParser(description="conda post extract tool used by installers")

    p.add_option('--skip-scripts',
                 action="store_true",
                 help="skip running pre/post-link scripts")

    p.add_option('--rm-dup',
                 action="store_true",
                 help="remove duplicates")

    opts, args = p.parse_args()
    if args:
        p.error('no arguments expected')

    if opts.skip_scripts:
        SKIP_SCRIPTS = True

    if opts.rm_dup:
        remove_duplicates()
        return

    post_extract()


def warn_on_special_chrs():
    if on_win:
        return
    for c in SPECIAL_ASCII:
        if c in ROOT_PREFIX:
            print("WARNING: found '%s' in install prefix." % c)


if __name__ == '__main__':
    if IDISTS:
        main()
        warn_on_special_chrs()
    else: # common usecase
        main2()
