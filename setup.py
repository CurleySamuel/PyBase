from __future__ import unicode_literals

from setuptools import find_packages, setup

setup(name='pybase',
      version='0.3.2',
      description='Native python client to hbase 1.0+',
      url='https://github.com/CurleySamuel/PyBase',
      author='Sam Curley',
      author_email='CurleySamuel@gmail.com',
      license='Apache License 2.0',
      packages=find_packages('.', exclude=['tests']),
      install_requires=["intervaltree  >= 3.0, < 4.0",
                        "kazoo", "six", "zope.interface", "protobuf"],
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
      ],
      zip_safe=False)
