# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Quota.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import HBase_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='Quota.proto',
  package='pb',
  serialized_pb=_b('\n\x0bQuota.proto\x12\x02pb\x1a\x0bHBase.proto\"x\n\nTimedQuota\x12\x1f\n\ttime_unit\x18\x01 \x02(\x0e\x32\x0c.pb.TimeUnit\x12\x12\n\nsoft_limit\x18\x02 \x01(\x04\x12\r\n\x05share\x18\x03 \x01(\x02\x12&\n\x05scope\x18\x04 \x01(\x0e\x32\x0e.pb.QuotaScope:\x07MACHINE\"\xd9\x01\n\x08Throttle\x12\x1f\n\x07req_num\x18\x01 \x01(\x0b\x32\x0e.pb.TimedQuota\x12 \n\x08req_size\x18\x02 \x01(\x0b\x32\x0e.pb.TimedQuota\x12!\n\twrite_num\x18\x03 \x01(\x0b\x32\x0e.pb.TimedQuota\x12\"\n\nwrite_size\x18\x04 \x01(\x0b\x32\x0e.pb.TimedQuota\x12 \n\x08read_num\x18\x05 \x01(\x0b\x32\x0e.pb.TimedQuota\x12!\n\tread_size\x18\x06 \x01(\x0b\x32\x0e.pb.TimedQuota\"V\n\x0fThrottleRequest\x12\x1e\n\x04type\x18\x01 \x01(\x0e\x32\x10.pb.ThrottleType\x12#\n\x0btimed_quota\x18\x02 \x01(\x0b\x32\x0e.pb.TimedQuota\"G\n\x06Quotas\x12\x1d\n\x0e\x62ypass_globals\x18\x01 \x01(\x08:\x05\x66\x61lse\x12\x1e\n\x08throttle\x18\x02 \x01(\x0b\x32\x0c.pb.Throttle\"\x0c\n\nQuotaUsage*&\n\nQuotaScope\x12\x0b\n\x07\x43LUSTER\x10\x01\x12\x0b\n\x07MACHINE\x10\x02*v\n\x0cThrottleType\x12\x12\n\x0eREQUEST_NUMBER\x10\x01\x12\x10\n\x0cREQUEST_SIZE\x10\x02\x12\x10\n\x0cWRITE_NUMBER\x10\x03\x12\x0e\n\nWRITE_SIZE\x10\x04\x12\x0f\n\x0bREAD_NUMBER\x10\x05\x12\r\n\tREAD_SIZE\x10\x06*\x19\n\tQuotaType\x12\x0c\n\x08THROTTLE\x10\x01\x42\x41\n*org.apache.hadoop.hbase.protobuf.generatedB\x0bQuotaProtosH\x01\x88\x01\x01\xa0\x01\x01')
  ,
  dependencies=[HBase_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_QUOTASCOPE = _descriptor.EnumDescriptor(
  name='QuotaScope',
  full_name='pb.QuotaScope',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='CLUSTER', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MACHINE', index=1, number=2,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=549,
  serialized_end=587,
)
_sym_db.RegisterEnumDescriptor(_QUOTASCOPE)

QuotaScope = enum_type_wrapper.EnumTypeWrapper(_QUOTASCOPE)
_THROTTLETYPE = _descriptor.EnumDescriptor(
  name='ThrottleType',
  full_name='pb.ThrottleType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='REQUEST_NUMBER', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='REQUEST_SIZE', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='WRITE_NUMBER', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='WRITE_SIZE', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='READ_NUMBER', index=4, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='READ_SIZE', index=5, number=6,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=589,
  serialized_end=707,
)
_sym_db.RegisterEnumDescriptor(_THROTTLETYPE)

ThrottleType = enum_type_wrapper.EnumTypeWrapper(_THROTTLETYPE)
_QUOTATYPE = _descriptor.EnumDescriptor(
  name='QuotaType',
  full_name='pb.QuotaType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='THROTTLE', index=0, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=709,
  serialized_end=734,
)
_sym_db.RegisterEnumDescriptor(_QUOTATYPE)

QuotaType = enum_type_wrapper.EnumTypeWrapper(_QUOTATYPE)
CLUSTER = 1
MACHINE = 2
REQUEST_NUMBER = 1
REQUEST_SIZE = 2
WRITE_NUMBER = 3
WRITE_SIZE = 4
READ_NUMBER = 5
READ_SIZE = 6
THROTTLE = 1



_TIMEDQUOTA = _descriptor.Descriptor(
  name='TimedQuota',
  full_name='pb.TimedQuota',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='time_unit', full_name='pb.TimedQuota.time_unit', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='soft_limit', full_name='pb.TimedQuota.soft_limit', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='share', full_name='pb.TimedQuota.share', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='scope', full_name='pb.TimedQuota.scope', index=3,
      number=4, type=14, cpp_type=8, label=1,
      has_default_value=True, default_value=2,
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
  serialized_start=32,
  serialized_end=152,
)


_THROTTLE = _descriptor.Descriptor(
  name='Throttle',
  full_name='pb.Throttle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='req_num', full_name='pb.Throttle.req_num', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='req_size', full_name='pb.Throttle.req_size', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='write_num', full_name='pb.Throttle.write_num', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='write_size', full_name='pb.Throttle.write_size', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='read_num', full_name='pb.Throttle.read_num', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='read_size', full_name='pb.Throttle.read_size', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=155,
  serialized_end=372,
)


_THROTTLEREQUEST = _descriptor.Descriptor(
  name='ThrottleRequest',
  full_name='pb.ThrottleRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='pb.ThrottleRequest.type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timed_quota', full_name='pb.ThrottleRequest.timed_quota', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=374,
  serialized_end=460,
)


_QUOTAS = _descriptor.Descriptor(
  name='Quotas',
  full_name='pb.Quotas',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bypass_globals', full_name='pb.Quotas.bypass_globals', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=True, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='throttle', full_name='pb.Quotas.throttle', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=462,
  serialized_end=533,
)


_QUOTAUSAGE = _descriptor.Descriptor(
  name='QuotaUsage',
  full_name='pb.QuotaUsage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
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
  serialized_start=535,
  serialized_end=547,
)

_TIMEDQUOTA.fields_by_name['time_unit'].enum_type = HBase_pb2._TIMEUNIT
_TIMEDQUOTA.fields_by_name['scope'].enum_type = _QUOTASCOPE
_THROTTLE.fields_by_name['req_num'].message_type = _TIMEDQUOTA
_THROTTLE.fields_by_name['req_size'].message_type = _TIMEDQUOTA
_THROTTLE.fields_by_name['write_num'].message_type = _TIMEDQUOTA
_THROTTLE.fields_by_name['write_size'].message_type = _TIMEDQUOTA
_THROTTLE.fields_by_name['read_num'].message_type = _TIMEDQUOTA
_THROTTLE.fields_by_name['read_size'].message_type = _TIMEDQUOTA
_THROTTLEREQUEST.fields_by_name['type'].enum_type = _THROTTLETYPE
_THROTTLEREQUEST.fields_by_name['timed_quota'].message_type = _TIMEDQUOTA
_QUOTAS.fields_by_name['throttle'].message_type = _THROTTLE
DESCRIPTOR.message_types_by_name['TimedQuota'] = _TIMEDQUOTA
DESCRIPTOR.message_types_by_name['Throttle'] = _THROTTLE
DESCRIPTOR.message_types_by_name['ThrottleRequest'] = _THROTTLEREQUEST
DESCRIPTOR.message_types_by_name['Quotas'] = _QUOTAS
DESCRIPTOR.message_types_by_name['QuotaUsage'] = _QUOTAUSAGE
DESCRIPTOR.enum_types_by_name['QuotaScope'] = _QUOTASCOPE
DESCRIPTOR.enum_types_by_name['ThrottleType'] = _THROTTLETYPE
DESCRIPTOR.enum_types_by_name['QuotaType'] = _QUOTATYPE

TimedQuota = _reflection.GeneratedProtocolMessageType('TimedQuota', (_message.Message,), dict(
  DESCRIPTOR = _TIMEDQUOTA,
  __module__ = 'Quota_pb2'
  # @@protoc_insertion_point(class_scope:pb.TimedQuota)
  ))
_sym_db.RegisterMessage(TimedQuota)

Throttle = _reflection.GeneratedProtocolMessageType('Throttle', (_message.Message,), dict(
  DESCRIPTOR = _THROTTLE,
  __module__ = 'Quota_pb2'
  # @@protoc_insertion_point(class_scope:pb.Throttle)
  ))
_sym_db.RegisterMessage(Throttle)

ThrottleRequest = _reflection.GeneratedProtocolMessageType('ThrottleRequest', (_message.Message,), dict(
  DESCRIPTOR = _THROTTLEREQUEST,
  __module__ = 'Quota_pb2'
  # @@protoc_insertion_point(class_scope:pb.ThrottleRequest)
  ))
_sym_db.RegisterMessage(ThrottleRequest)

Quotas = _reflection.GeneratedProtocolMessageType('Quotas', (_message.Message,), dict(
  DESCRIPTOR = _QUOTAS,
  __module__ = 'Quota_pb2'
  # @@protoc_insertion_point(class_scope:pb.Quotas)
  ))
_sym_db.RegisterMessage(Quotas)

QuotaUsage = _reflection.GeneratedProtocolMessageType('QuotaUsage', (_message.Message,), dict(
  DESCRIPTOR = _QUOTAUSAGE,
  __module__ = 'Quota_pb2'
  # @@protoc_insertion_point(class_scope:pb.QuotaUsage)
  ))
_sym_db.RegisterMessage(QuotaUsage)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*org.apache.hadoop.hbase.protobuf.generatedB\013QuotaProtosH\001\210\001\001\240\001\001'))
# @@protoc_insertion_point(module_scope)
