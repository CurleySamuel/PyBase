# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: FS.proto

from __future__ import absolute_import, print_function

import sys

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='FS.proto',
  package='pb',
  serialized_pb=_b('\n\x08\x46S.proto\x12\x02pb\"*\n\x17HBaseVersionFileContent\x12\x0f\n\x07version\x18\x01 \x02(\t\"_\n\tReference\x12\x10\n\x08splitkey\x18\x01 \x02(\x0c\x12\"\n\x05range\x18\x02 \x02(\x0e\x32\x13.pb.Reference.Range\"\x1c\n\x05Range\x12\x07\n\x03TOP\x10\x00\x12\n\n\x06\x42OTTOM\x10\x01\x42;\n*org.apache.hadoop.hbase.protobuf.generatedB\x08\x46SProtosH\x01\xa0\x01\x01')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_REFERENCE_RANGE = _descriptor.EnumDescriptor(
  name='Range',
  full_name='pb.Reference.Range',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='TOP', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='BOTTOM', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=127,
  serialized_end=155,
)
_sym_db.RegisterEnumDescriptor(_REFERENCE_RANGE)


_HBASEVERSIONFILECONTENT = _descriptor.Descriptor(
  name='HBaseVersionFileContent',
  full_name='pb.HBaseVersionFileContent',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='version', full_name='pb.HBaseVersionFileContent.version', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=16,
  serialized_end=58,
)


_REFERENCE = _descriptor.Descriptor(
  name='Reference',
  full_name='pb.Reference',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='splitkey', full_name='pb.Reference.splitkey', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='range', full_name='pb.Reference.range', index=1,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _REFERENCE_RANGE,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=60,
  serialized_end=155,
)

_REFERENCE.fields_by_name['range'].enum_type = _REFERENCE_RANGE
_REFERENCE_RANGE.containing_type = _REFERENCE
DESCRIPTOR.message_types_by_name['HBaseVersionFileContent'] = _HBASEVERSIONFILECONTENT
DESCRIPTOR.message_types_by_name['Reference'] = _REFERENCE

HBaseVersionFileContent = _reflection.GeneratedProtocolMessageType('HBaseVersionFileContent', (_message.Message,), dict(
  DESCRIPTOR = _HBASEVERSIONFILECONTENT,
  __module__ = 'FS_pb2'
  # @@protoc_insertion_point(class_scope:pb.HBaseVersionFileContent)
  ))
_sym_db.RegisterMessage(HBaseVersionFileContent)

Reference = _reflection.GeneratedProtocolMessageType('Reference', (_message.Message,), dict(
  DESCRIPTOR = _REFERENCE,
  __module__ = 'FS_pb2'
  # @@protoc_insertion_point(class_scope:pb.Reference)
  ))
_sym_db.RegisterMessage(Reference)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*org.apache.hadoop.hbase.protobuf.generatedB\010FSProtosH\001\240\001\001'))
# @@protoc_insertion_point(module_scope)