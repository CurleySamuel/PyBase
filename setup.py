from setuptools import find_packages, setup

setup(name='pybase',
      version='0.2',
      description='Native python client to hbase 1.0+',
      url='https://github.com/CurleySamuel/PyBase',
      author='Sam Curley',
      author_email='CurleySamuel@gmail.com',
      license='Apache License 2.0',
      packages=find_packages('.', exclude=['tests']),
      install_requires=["intervaltree", "kazoo", "six", "zope.interface", "protobuf"],
      zip_safe=False)
