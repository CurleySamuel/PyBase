# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ClusterId.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ClusterId.proto',
  package='pb',
  serialized_pb=_b('\n\x0f\x43lusterId.proto\x12\x02pb\"\x1f\n\tClusterId\x12\x12\n\ncluster_id\x18\x01 \x02(\tBB\n*org.apache.hadoop.hbase.protobuf.generatedB\x0f\x43lusterIdProtosH\x01\xa0\x01\x01')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_CLUSTERID = _descriptor.Descriptor(
  name='ClusterId',
  full_name='pb.ClusterId',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='cluster_id', full_name='pb.ClusterId.cluster_id', index=0,
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
  serialized_start=23,
  serialized_end=54,
)

DESCRIPTOR.message_types_by_name['ClusterId'] = _CLUSTERID

ClusterId = _reflection.GeneratedProtocolMessageType('ClusterId', (_message.Message,), dict(
  DESCRIPTOR = _CLUSTERID,
  __module__ = 'ClusterId_pb2'
  # @@protoc_insertion_point(class_scope:pb.ClusterId)
  ))
_sym_db.RegisterMessage(ClusterId)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*org.apache.hadoop.hbase.protobuf.generatedB\017ClusterIdProtosH\001\240\001\001'))
# @@protoc_insertion_point(module_scope)
