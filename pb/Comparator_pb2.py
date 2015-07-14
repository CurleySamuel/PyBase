# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Comparator.proto

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
  name='Comparator.proto',
  package='pb',
  serialized_pb=_b('\n\x10\x43omparator.proto\x12\x02pb\"9\n\nComparator\x12\x0c\n\x04name\x18\x01 \x02(\t\x12\x1d\n\x15serialized_comparator\x18\x02 \x01(\x0c\"$\n\x13\x42yteArrayComparable\x12\r\n\x05value\x18\x01 \x01(\x0c\"?\n\x10\x42inaryComparator\x12+\n\ncomparable\x18\x01 \x02(\x0b\x32\x17.pb.ByteArrayComparable\"=\n\x0eLongComparator\x12+\n\ncomparable\x18\x01 \x02(\x0b\x32\x17.pb.ByteArrayComparable\"E\n\x16\x42inaryPrefixComparator\x12+\n\ncomparable\x18\x01 \x02(\x0b\x32\x17.pb.ByteArrayComparable\"\x94\x01\n\rBitComparator\x12+\n\ncomparable\x18\x01 \x02(\x0b\x32\x17.pb.ByteArrayComparable\x12/\n\nbitwise_op\x18\x02 \x02(\x0e\x32\x1b.pb.BitComparator.BitwiseOp\"%\n\tBitwiseOp\x12\x07\n\x03\x41ND\x10\x01\x12\x06\n\x02OR\x10\x02\x12\x07\n\x03XOR\x10\x03\"\x10\n\x0eNullComparator\"`\n\x15RegexStringComparator\x12\x0f\n\x07pattern\x18\x01 \x02(\t\x12\x15\n\rpattern_flags\x18\x02 \x02(\x05\x12\x0f\n\x07\x63harset\x18\x03 \x02(\t\x12\x0e\n\x06\x65ngine\x18\x04 \x01(\t\"%\n\x13SubstringComparator\x12\x0e\n\x06substr\x18\x01 \x02(\tBF\n*org.apache.hadoop.hbase.protobuf.generatedB\x10\x43omparatorProtosH\x01\x88\x01\x01\xa0\x01\x01')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_BITCOMPARATOR_BITWISEOP = _descriptor.EnumDescriptor(
  name='BitwiseOp',
  full_name='pb.BitComparator.BitwiseOp',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='AND', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='OR', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='XOR', index=2, number=3,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=432,
  serialized_end=469,
)
_sym_db.RegisterEnumDescriptor(_BITCOMPARATOR_BITWISEOP)


_COMPARATOR = _descriptor.Descriptor(
  name='Comparator',
  full_name='pb.Comparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='pb.Comparator.name', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='serialized_comparator', full_name='pb.Comparator.serialized_comparator', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
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
  serialized_start=24,
  serialized_end=81,
)


_BYTEARRAYCOMPARABLE = _descriptor.Descriptor(
  name='ByteArrayComparable',
  full_name='pb.ByteArrayComparable',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='pb.ByteArrayComparable.value', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
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
  serialized_start=83,
  serialized_end=119,
)


_BINARYCOMPARATOR = _descriptor.Descriptor(
  name='BinaryComparator',
  full_name='pb.BinaryComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='comparable', full_name='pb.BinaryComparator.comparable', index=0,
      number=1, type=11, cpp_type=10, label=2,
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
  serialized_start=121,
  serialized_end=184,
)


_LONGCOMPARATOR = _descriptor.Descriptor(
  name='LongComparator',
  full_name='pb.LongComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='comparable', full_name='pb.LongComparator.comparable', index=0,
      number=1, type=11, cpp_type=10, label=2,
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
  serialized_start=186,
  serialized_end=247,
)


_BINARYPREFIXCOMPARATOR = _descriptor.Descriptor(
  name='BinaryPrefixComparator',
  full_name='pb.BinaryPrefixComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='comparable', full_name='pb.BinaryPrefixComparator.comparable', index=0,
      number=1, type=11, cpp_type=10, label=2,
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
  serialized_start=249,
  serialized_end=318,
)


_BITCOMPARATOR = _descriptor.Descriptor(
  name='BitComparator',
  full_name='pb.BitComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='comparable', full_name='pb.BitComparator.comparable', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='bitwise_op', full_name='pb.BitComparator.bitwise_op', index=1,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _BITCOMPARATOR_BITWISEOP,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=321,
  serialized_end=469,
)


_NULLCOMPARATOR = _descriptor.Descriptor(
  name='NullComparator',
  full_name='pb.NullComparator',
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
  serialized_start=471,
  serialized_end=487,
)


_REGEXSTRINGCOMPARATOR = _descriptor.Descriptor(
  name='RegexStringComparator',
  full_name='pb.RegexStringComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='pattern', full_name='pb.RegexStringComparator.pattern', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='pattern_flags', full_name='pb.RegexStringComparator.pattern_flags', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='charset', full_name='pb.RegexStringComparator.charset', index=2,
      number=3, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='engine', full_name='pb.RegexStringComparator.engine', index=3,
      number=4, type=9, cpp_type=9, label=1,
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
  serialized_start=489,
  serialized_end=585,
)


_SUBSTRINGCOMPARATOR = _descriptor.Descriptor(
  name='SubstringComparator',
  full_name='pb.SubstringComparator',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='substr', full_name='pb.SubstringComparator.substr', index=0,
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
  serialized_start=587,
  serialized_end=624,
)

_BINARYCOMPARATOR.fields_by_name['comparable'].message_type = _BYTEARRAYCOMPARABLE
_LONGCOMPARATOR.fields_by_name['comparable'].message_type = _BYTEARRAYCOMPARABLE
_BINARYPREFIXCOMPARATOR.fields_by_name['comparable'].message_type = _BYTEARRAYCOMPARABLE
_BITCOMPARATOR.fields_by_name['comparable'].message_type = _BYTEARRAYCOMPARABLE
_BITCOMPARATOR.fields_by_name['bitwise_op'].enum_type = _BITCOMPARATOR_BITWISEOP
_BITCOMPARATOR_BITWISEOP.containing_type = _BITCOMPARATOR
DESCRIPTOR.message_types_by_name['Comparator'] = _COMPARATOR
DESCRIPTOR.message_types_by_name['ByteArrayComparable'] = _BYTEARRAYCOMPARABLE
DESCRIPTOR.message_types_by_name['BinaryComparator'] = _BINARYCOMPARATOR
DESCRIPTOR.message_types_by_name['LongComparator'] = _LONGCOMPARATOR
DESCRIPTOR.message_types_by_name['BinaryPrefixComparator'] = _BINARYPREFIXCOMPARATOR
DESCRIPTOR.message_types_by_name['BitComparator'] = _BITCOMPARATOR
DESCRIPTOR.message_types_by_name['NullComparator'] = _NULLCOMPARATOR
DESCRIPTOR.message_types_by_name['RegexStringComparator'] = _REGEXSTRINGCOMPARATOR
DESCRIPTOR.message_types_by_name['SubstringComparator'] = _SUBSTRINGCOMPARATOR

Comparator = _reflection.GeneratedProtocolMessageType('Comparator', (_message.Message,), dict(
  DESCRIPTOR = _COMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.Comparator)
  ))
_sym_db.RegisterMessage(Comparator)

ByteArrayComparable = _reflection.GeneratedProtocolMessageType('ByteArrayComparable', (_message.Message,), dict(
  DESCRIPTOR = _BYTEARRAYCOMPARABLE,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.ByteArrayComparable)
  ))
_sym_db.RegisterMessage(ByteArrayComparable)

BinaryComparator = _reflection.GeneratedProtocolMessageType('BinaryComparator', (_message.Message,), dict(
  DESCRIPTOR = _BINARYCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.BinaryComparator)
  ))
_sym_db.RegisterMessage(BinaryComparator)

LongComparator = _reflection.GeneratedProtocolMessageType('LongComparator', (_message.Message,), dict(
  DESCRIPTOR = _LONGCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.LongComparator)
  ))
_sym_db.RegisterMessage(LongComparator)

BinaryPrefixComparator = _reflection.GeneratedProtocolMessageType('BinaryPrefixComparator', (_message.Message,), dict(
  DESCRIPTOR = _BINARYPREFIXCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.BinaryPrefixComparator)
  ))
_sym_db.RegisterMessage(BinaryPrefixComparator)

BitComparator = _reflection.GeneratedProtocolMessageType('BitComparator', (_message.Message,), dict(
  DESCRIPTOR = _BITCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.BitComparator)
  ))
_sym_db.RegisterMessage(BitComparator)

NullComparator = _reflection.GeneratedProtocolMessageType('NullComparator', (_message.Message,), dict(
  DESCRIPTOR = _NULLCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.NullComparator)
  ))
_sym_db.RegisterMessage(NullComparator)

RegexStringComparator = _reflection.GeneratedProtocolMessageType('RegexStringComparator', (_message.Message,), dict(
  DESCRIPTOR = _REGEXSTRINGCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.RegexStringComparator)
  ))
_sym_db.RegisterMessage(RegexStringComparator)

SubstringComparator = _reflection.GeneratedProtocolMessageType('SubstringComparator', (_message.Message,), dict(
  DESCRIPTOR = _SUBSTRINGCOMPARATOR,
  __module__ = 'Comparator_pb2'
  # @@protoc_insertion_point(class_scope:pb.SubstringComparator)
  ))
_sym_db.RegisterMessage(SubstringComparator)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*org.apache.hadoop.hbase.protobuf.generatedB\020ComparatorProtosH\001\210\001\001\240\001\001'))
# @@protoc_insertion_point(module_scope)
