from distutils.core import setup

setup(name='pybase',
      version='0.1',
      description='Native python client to hbase 1.0+',
      url='https://github.com/CurleySamuel/PyBase',
      author='Sam Curley',
      author_email='CurleySamuel@gmail.com',
      license='Apache License 2.0',
      packages=['pybase', 'pybase.zk', 'pybase.pb', 'pybase.request',
                'pybase.region',  'pybase.helpers'],
      package_dir={'pybase': '.'},
      install_requires=["intervaltree","kazoo","six", "zope.interface", "protobuf"],
      zip_safe=False)
