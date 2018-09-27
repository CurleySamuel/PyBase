# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ClusterStatus.proto

from __future__ import absolute_import, print_function

import sys

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pb2
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

from . import ClusterId_pb2
from . import FS_pb2
from . import HBase_pb2

_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ClusterStatus.proto',
  package='pb',
  serialized_pb=_b('\n\x13\x43lusterStatus.proto\x12\x02pb\x1a\x0bHBase.proto\x1a\x0f\x43lusterId.proto\x1a\x08\x46S.proto\"\xcd\x02\n\x0bRegionState\x12#\n\x0bregion_info\x18\x01 \x02(\x0b\x32\x0e.pb.RegionInfo\x12$\n\x05state\x18\x02 \x02(\x0e\x32\x15.pb.RegionState.State\x12\r\n\x05stamp\x18\x03 \x01(\x04\"\xe3\x01\n\x05State\x12\x0b\n\x07OFFLINE\x10\x00\x12\x10\n\x0cPENDING_OPEN\x10\x01\x12\x0b\n\x07OPENING\x10\x02\x12\x08\n\x04OPEN\x10\x03\x12\x11\n\rPENDING_CLOSE\x10\x04\x12\x0b\n\x07\x43LOSING\x10\x05\x12\n\n\x06\x43LOSED\x10\x06\x12\r\n\tSPLITTING\x10\x07\x12\t\n\x05SPLIT\x10\x08\x12\x0f\n\x0b\x46\x41ILED_OPEN\x10\t\x12\x10\n\x0c\x46\x41ILED_CLOSE\x10\n\x12\x0b\n\x07MERGING\x10\x0b\x12\n\n\x06MERGED\x10\x0c\x12\x11\n\rSPLITTING_NEW\x10\r\x12\x0f\n\x0bMERGING_NEW\x10\x0e\"^\n\x12RegionInTransition\x12!\n\x04spec\x18\x01 \x02(\x0b\x32\x13.pb.RegionSpecifier\x12%\n\x0cregion_state\x18\x02 \x02(\x0b\x32\x0f.pb.RegionState\";\n\x0fStoreSequenceId\x12\x13\n\x0b\x66\x61mily_name\x18\x01 \x02(\x0c\x12\x13\n\x0bsequence_id\x18\x02 \x02(\x04\"j\n\x16RegionStoreSequenceIds\x12 \n\x18last_flushed_sequence_id\x18\x01 \x02(\x04\x12.\n\x11store_sequence_id\x18\x02 \x03(\x0b\x32\x13.pb.StoreSequenceId\"\xc8\x04\n\nRegionLoad\x12-\n\x10region_specifier\x18\x01 \x02(\x0b\x32\x13.pb.RegionSpecifier\x12\x0e\n\x06stores\x18\x02 \x01(\r\x12\x12\n\nstorefiles\x18\x03 \x01(\r\x12\"\n\x1astore_uncompressed_size_MB\x18\x04 \x01(\r\x12\x19\n\x11storefile_size_MB\x18\x05 \x01(\r\x12\x18\n\x10memstore_size_MB\x18\x06 \x01(\r\x12\x1f\n\x17storefile_index_size_MB\x18\x07 \x01(\r\x12\x1b\n\x13read_requests_count\x18\x08 \x01(\x04\x12\x1c\n\x14write_requests_count\x18\t \x01(\x04\x12\x1c\n\x14total_compacting_KVs\x18\n \x01(\x04\x12\x1d\n\x15\x63urrent_compacted_KVs\x18\x0b \x01(\x04\x12\x1a\n\x12root_index_size_KB\x18\x0c \x01(\r\x12\"\n\x1atotal_static_index_size_KB\x18\r \x01(\r\x12\"\n\x1atotal_static_bloom_size_KB\x18\x0e \x01(\r\x12\x1c\n\x14\x63omplete_sequence_id\x18\x0f \x01(\x04\x12\x15\n\rdata_locality\x18\x10 \x01(\x02\x12#\n\x18last_major_compaction_ts\x18\x11 \x01(\x04:\x01\x30\x12\x37\n\x1astore_complete_sequence_id\x18\x12 \x03(\x0b\x32\x13.pb.StoreSequenceId\"T\n\x13ReplicationLoadSink\x12\x1a\n\x12\x61geOfLastAppliedOp\x18\x01 \x02(\x04\x12!\n\x19timeStampsOfLastAppliedOp\x18\x02 \x02(\x04\"\x95\x01\n\x15ReplicationLoadSource\x12\x0e\n\x06peerID\x18\x01 \x02(\t\x12\x1a\n\x12\x61geOfLastShippedOp\x18\x02 \x02(\x04\x12\x16\n\x0esizeOfLogQueue\x18\x03 \x02(\r\x12 \n\x18timeStampOfLastShippedOp\x18\x04 \x02(\x04\x12\x16\n\x0ereplicationLag\x18\x05 \x02(\x04\"\xf2\x02\n\nServerLoad\x12\x1a\n\x12number_of_requests\x18\x01 \x01(\x04\x12 \n\x18total_number_of_requests\x18\x02 \x01(\x04\x12\x14\n\x0cused_heap_MB\x18\x03 \x01(\r\x12\x13\n\x0bmax_heap_MB\x18\x04 \x01(\r\x12$\n\x0cregion_loads\x18\x05 \x03(\x0b\x32\x0e.pb.RegionLoad\x12%\n\x0c\x63oprocessors\x18\x06 \x03(\x0b\x32\x0f.pb.Coprocessor\x12\x19\n\x11report_start_time\x18\x07 \x01(\x04\x12\x17\n\x0freport_end_time\x18\x08 \x01(\x04\x12\x18\n\x10info_server_port\x18\t \x01(\r\x12\x31\n\x0ereplLoadSource\x18\n \x03(\x0b\x32\x19.pb.ReplicationLoadSource\x12-\n\x0creplLoadSink\x18\x0b \x01(\x0b\x32\x17.pb.ReplicationLoadSink\"U\n\x0eLiveServerInfo\x12\x1e\n\x06server\x18\x01 \x02(\x0b\x32\x0e.pb.ServerName\x12#\n\x0bserver_load\x18\x02 \x02(\x0b\x32\x0e.pb.ServerLoad\"\xf8\x02\n\rClusterStatus\x12\x32\n\rhbase_version\x18\x01 \x01(\x0b\x32\x1b.pb.HBaseVersionFileContent\x12(\n\x0clive_servers\x18\x02 \x03(\x0b\x32\x12.pb.LiveServerInfo\x12$\n\x0c\x64\x65\x61\x64_servers\x18\x03 \x03(\x0b\x32\x0e.pb.ServerName\x12\x35\n\x15regions_in_transition\x18\x04 \x03(\x0b\x32\x16.pb.RegionInTransition\x12!\n\ncluster_id\x18\x05 \x01(\x0b\x32\r.pb.ClusterId\x12,\n\x13master_coprocessors\x18\x06 \x03(\x0b\x32\x0f.pb.Coprocessor\x12\x1e\n\x06master\x18\x07 \x01(\x0b\x32\x0e.pb.ServerName\x12&\n\x0e\x62\x61\x63kup_masters\x18\x08 \x03(\x0b\x32\x0e.pb.ServerName\x12\x13\n\x0b\x62\x61lancer_on\x18\t \x01(\x08\x42\x46\n*org.apache.hadoop.hbase.protobuf.generatedB\x13\x43lusterStatusProtosH\x01\xa0\x01\x01')
  ,
  dependencies=[HBase_pb2.DESCRIPTOR,ClusterId_pb2.DESCRIPTOR,FS_pb2.DESCRIPTOR,])
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_REGIONSTATE_STATE = _descriptor.EnumDescriptor(
  name='State',
  full_name='pb.RegionState.State',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OFFLINE', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PENDING_OPEN', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='OPENING', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='OPEN', index=3, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PENDING_CLOSE', index=4, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CLOSING', index=5, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CLOSED', index=6, number=6,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SPLITTING', index=7, number=7,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SPLIT', index=8, number=8,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='FAILED_OPEN', index=9, number=9,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='FAILED_CLOSE', index=10, number=10,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MERGING', index=11, number=11,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MERGED', index=12, number=12,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SPLITTING_NEW', index=13, number=13,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MERGING_NEW', index=14, number=14,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=174,
  serialized_end=401,
)
_sym_db.RegisterEnumDescriptor(_REGIONSTATE_STATE)


_REGIONSTATE = _descriptor.Descriptor(
  name='RegionState',
  full_name='pb.RegionState',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='region_info', full_name='pb.RegionState.region_info', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='state', full_name='pb.RegionState.state', index=1,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='stamp', full_name='pb.RegionState.stamp', index=2,
      number=3, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _REGIONSTATE_STATE,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=68,
  serialized_end=401,
)


_REGIONINTRANSITION = _descriptor.Descriptor(
  name='RegionInTransition',
  full_name='pb.RegionInTransition',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='spec', full_name='pb.RegionInTransition.spec', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='region_state', full_name='pb.RegionInTransition.region_state', index=1,
      number=2, type=11, cpp_type=10, label=2,
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
  serialized_start=403,
  serialized_end=497,
)


_STORESEQUENCEID = _descriptor.Descriptor(
  name='StoreSequenceId',
  full_name='pb.StoreSequenceId',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='family_name', full_name='pb.StoreSequenceId.family_name', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sequence_id', full_name='pb.StoreSequenceId.sequence_id', index=1,
      number=2, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=499,
  serialized_end=558,
)


_REGIONSTORESEQUENCEIDS = _descriptor.Descriptor(
  name='RegionStoreSequenceIds',
  full_name='pb.RegionStoreSequenceIds',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='last_flushed_sequence_id', full_name='pb.RegionStoreSequenceIds.last_flushed_sequence_id', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='store_sequence_id', full_name='pb.RegionStoreSequenceIds.store_sequence_id', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=560,
  serialized_end=666,
)


_REGIONLOAD = _descriptor.Descriptor(
  name='RegionLoad',
  full_name='pb.RegionLoad',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='region_specifier', full_name='pb.RegionLoad.region_specifier', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='stores', full_name='pb.RegionLoad.stores', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='storefiles', full_name='pb.RegionLoad.storefiles', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='store_uncompressed_size_MB', full_name='pb.RegionLoad.store_uncompressed_size_MB', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='storefile_size_MB', full_name='pb.RegionLoad.storefile_size_MB', index=4,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='memstore_size_MB', full_name='pb.RegionLoad.memstore_size_MB', index=5,
      number=6, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='storefile_index_size_MB', full_name='pb.RegionLoad.storefile_index_size_MB', index=6,
      number=7, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='read_requests_count', full_name='pb.RegionLoad.read_requests_count', index=7,
      number=8, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='write_requests_count', full_name='pb.RegionLoad.write_requests_count', index=8,
      number=9, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_compacting_KVs', full_name='pb.RegionLoad.total_compacting_KVs', index=9,
      number=10, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='current_compacted_KVs', full_name='pb.RegionLoad.current_compacted_KVs', index=10,
      number=11, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='root_index_size_KB', full_name='pb.RegionLoad.root_index_size_KB', index=11,
      number=12, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_static_index_size_KB', full_name='pb.RegionLoad.total_static_index_size_KB', index=12,
      number=13, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_static_bloom_size_KB', full_name='pb.RegionLoad.total_static_bloom_size_KB', index=13,
      number=14, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='complete_sequence_id', full_name='pb.RegionLoad.complete_sequence_id', index=14,
      number=15, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='data_locality', full_name='pb.RegionLoad.data_locality', index=15,
      number=16, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='last_major_compaction_ts', full_name='pb.RegionLoad.last_major_compaction_ts', index=16,
      number=17, type=4, cpp_type=4, label=1,
      has_default_value=True, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='store_complete_sequence_id', full_name='pb.RegionLoad.store_complete_sequence_id', index=17,
      number=18, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=669,
  serialized_end=1253,
)


_REPLICATIONLOADSINK = _descriptor.Descriptor(
  name='ReplicationLoadSink',
  full_name='pb.ReplicationLoadSink',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ageOfLastAppliedOp', full_name='pb.ReplicationLoadSink.ageOfLastAppliedOp', index=0,
      number=1, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timeStampsOfLastAppliedOp', full_name='pb.ReplicationLoadSink.timeStampsOfLastAppliedOp', index=1,
      number=2, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=1255,
  serialized_end=1339,
)


_REPLICATIONLOADSOURCE = _descriptor.Descriptor(
  name='ReplicationLoadSource',
  full_name='pb.ReplicationLoadSource',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='peerID', full_name='pb.ReplicationLoadSource.peerID', index=0,
      number=1, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='ageOfLastShippedOp', full_name='pb.ReplicationLoadSource.ageOfLastShippedOp', index=1,
      number=2, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='sizeOfLogQueue', full_name='pb.ReplicationLoadSource.sizeOfLogQueue', index=2,
      number=3, type=13, cpp_type=3, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='timeStampOfLastShippedOp', full_name='pb.ReplicationLoadSource.timeStampOfLastShippedOp', index=3,
      number=4, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='replicationLag', full_name='pb.ReplicationLoadSource.replicationLag', index=4,
      number=5, type=4, cpp_type=4, label=2,
      has_default_value=False, default_value=0,
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
  serialized_start=1342,
  serialized_end=1491,
)


_SERVERLOAD = _descriptor.Descriptor(
  name='ServerLoad',
  full_name='pb.ServerLoad',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='number_of_requests', full_name='pb.ServerLoad.number_of_requests', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='total_number_of_requests', full_name='pb.ServerLoad.total_number_of_requests', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='used_heap_MB', full_name='pb.ServerLoad.used_heap_MB', index=2,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='max_heap_MB', full_name='pb.ServerLoad.max_heap_MB', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='region_loads', full_name='pb.ServerLoad.region_loads', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='coprocessors', full_name='pb.ServerLoad.coprocessors', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='report_start_time', full_name='pb.ServerLoad.report_start_time', index=6,
      number=7, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='report_end_time', full_name='pb.ServerLoad.report_end_time', index=7,
      number=8, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='info_server_port', full_name='pb.ServerLoad.info_server_port', index=8,
      number=9, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='replLoadSource', full_name='pb.ServerLoad.replLoadSource', index=9,
      number=10, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='replLoadSink', full_name='pb.ServerLoad.replLoadSink', index=10,
      number=11, type=11, cpp_type=10, label=1,
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
  serialized_start=1494,
  serialized_end=1864,
)


_LIVESERVERINFO = _descriptor.Descriptor(
  name='LiveServerInfo',
  full_name='pb.LiveServerInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='server', full_name='pb.LiveServerInfo.server', index=0,
      number=1, type=11, cpp_type=10, label=2,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='server_load', full_name='pb.LiveServerInfo.server_load', index=1,
      number=2, type=11, cpp_type=10, label=2,
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
  serialized_start=1866,
  serialized_end=1951,
)


_CLUSTERSTATUS = _descriptor.Descriptor(
  name='ClusterStatus',
  full_name='pb.ClusterStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hbase_version', full_name='pb.ClusterStatus.hbase_version', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='live_servers', full_name='pb.ClusterStatus.live_servers', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='dead_servers', full_name='pb.ClusterStatus.dead_servers', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='regions_in_transition', full_name='pb.ClusterStatus.regions_in_transition', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='cluster_id', full_name='pb.ClusterStatus.cluster_id', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='master_coprocessors', full_name='pb.ClusterStatus.master_coprocessors', index=5,
      number=6, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='master', full_name='pb.ClusterStatus.master', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='backup_masters', full_name='pb.ClusterStatus.backup_masters', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='balancer_on', full_name='pb.ClusterStatus.balancer_on', index=8,
      number=9, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
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
  serialized_start=1954,
  serialized_end=2330,
)

_REGIONSTATE.fields_by_name['region_info'].message_type = HBase_pb2._REGIONINFO
_REGIONSTATE.fields_by_name['state'].enum_type = _REGIONSTATE_STATE
_REGIONSTATE_STATE.containing_type = _REGIONSTATE
_REGIONINTRANSITION.fields_by_name['spec'].message_type = HBase_pb2._REGIONSPECIFIER
_REGIONINTRANSITION.fields_by_name['region_state'].message_type = _REGIONSTATE
_REGIONSTORESEQUENCEIDS.fields_by_name['store_sequence_id'].message_type = _STORESEQUENCEID
_REGIONLOAD.fields_by_name['region_specifier'].message_type = HBase_pb2._REGIONSPECIFIER
_REGIONLOAD.fields_by_name['store_complete_sequence_id'].message_type = _STORESEQUENCEID
_SERVERLOAD.fields_by_name['region_loads'].message_type = _REGIONLOAD
_SERVERLOAD.fields_by_name['coprocessors'].message_type = HBase_pb2._COPROCESSOR
_SERVERLOAD.fields_by_name['replLoadSource'].message_type = _REPLICATIONLOADSOURCE
_SERVERLOAD.fields_by_name['replLoadSink'].message_type = _REPLICATIONLOADSINK
_LIVESERVERINFO.fields_by_name['server'].message_type = HBase_pb2._SERVERNAME
_LIVESERVERINFO.fields_by_name['server_load'].message_type = _SERVERLOAD
_CLUSTERSTATUS.fields_by_name['hbase_version'].message_type = FS_pb2._HBASEVERSIONFILECONTENT
_CLUSTERSTATUS.fields_by_name['live_servers'].message_type = _LIVESERVERINFO
_CLUSTERSTATUS.fields_by_name['dead_servers'].message_type = HBase_pb2._SERVERNAME
_CLUSTERSTATUS.fields_by_name['regions_in_transition'].message_type = _REGIONINTRANSITION
_CLUSTERSTATUS.fields_by_name['cluster_id'].message_type = ClusterId_pb2._CLUSTERID
_CLUSTERSTATUS.fields_by_name['master_coprocessors'].message_type = HBase_pb2._COPROCESSOR
_CLUSTERSTATUS.fields_by_name['master'].message_type = HBase_pb2._SERVERNAME
_CLUSTERSTATUS.fields_by_name['backup_masters'].message_type = HBase_pb2._SERVERNAME
DESCRIPTOR.message_types_by_name['RegionState'] = _REGIONSTATE
DESCRIPTOR.message_types_by_name['RegionInTransition'] = _REGIONINTRANSITION
DESCRIPTOR.message_types_by_name['StoreSequenceId'] = _STORESEQUENCEID
DESCRIPTOR.message_types_by_name['RegionStoreSequenceIds'] = _REGIONSTORESEQUENCEIDS
DESCRIPTOR.message_types_by_name['RegionLoad'] = _REGIONLOAD
DESCRIPTOR.message_types_by_name['ReplicationLoadSink'] = _REPLICATIONLOADSINK
DESCRIPTOR.message_types_by_name['ReplicationLoadSource'] = _REPLICATIONLOADSOURCE
DESCRIPTOR.message_types_by_name['ServerLoad'] = _SERVERLOAD
DESCRIPTOR.message_types_by_name['LiveServerInfo'] = _LIVESERVERINFO
DESCRIPTOR.message_types_by_name['ClusterStatus'] = _CLUSTERSTATUS

RegionState = _reflection.GeneratedProtocolMessageType('RegionState', (_message.Message,), dict(
  DESCRIPTOR = _REGIONSTATE,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.RegionState)
  ))
_sym_db.RegisterMessage(RegionState)

RegionInTransition = _reflection.GeneratedProtocolMessageType('RegionInTransition', (_message.Message,), dict(
  DESCRIPTOR = _REGIONINTRANSITION,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.RegionInTransition)
  ))
_sym_db.RegisterMessage(RegionInTransition)

StoreSequenceId = _reflection.GeneratedProtocolMessageType('StoreSequenceId', (_message.Message,), dict(
  DESCRIPTOR = _STORESEQUENCEID,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.StoreSequenceId)
  ))
_sym_db.RegisterMessage(StoreSequenceId)

RegionStoreSequenceIds = _reflection.GeneratedProtocolMessageType('RegionStoreSequenceIds', (_message.Message,), dict(
  DESCRIPTOR = _REGIONSTORESEQUENCEIDS,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.RegionStoreSequenceIds)
  ))
_sym_db.RegisterMessage(RegionStoreSequenceIds)

RegionLoad = _reflection.GeneratedProtocolMessageType('RegionLoad', (_message.Message,), dict(
  DESCRIPTOR = _REGIONLOAD,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.RegionLoad)
  ))
_sym_db.RegisterMessage(RegionLoad)

ReplicationLoadSink = _reflection.GeneratedProtocolMessageType('ReplicationLoadSink', (_message.Message,), dict(
  DESCRIPTOR = _REPLICATIONLOADSINK,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.ReplicationLoadSink)
  ))
_sym_db.RegisterMessage(ReplicationLoadSink)

ReplicationLoadSource = _reflection.GeneratedProtocolMessageType('ReplicationLoadSource', (_message.Message,), dict(
  DESCRIPTOR = _REPLICATIONLOADSOURCE,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.ReplicationLoadSource)
  ))
_sym_db.RegisterMessage(ReplicationLoadSource)

ServerLoad = _reflection.GeneratedProtocolMessageType('ServerLoad', (_message.Message,), dict(
  DESCRIPTOR = _SERVERLOAD,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.ServerLoad)
  ))
_sym_db.RegisterMessage(ServerLoad)

LiveServerInfo = _reflection.GeneratedProtocolMessageType('LiveServerInfo', (_message.Message,), dict(
  DESCRIPTOR = _LIVESERVERINFO,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.LiveServerInfo)
  ))
_sym_db.RegisterMessage(LiveServerInfo)

ClusterStatus = _reflection.GeneratedProtocolMessageType('ClusterStatus', (_message.Message,), dict(
  DESCRIPTOR = _CLUSTERSTATUS,
  __module__ = 'ClusterStatus_pb2'
  # @@protoc_insertion_point(class_scope:pb.ClusterStatus)
  ))
_sym_db.RegisterMessage(ClusterStatus)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n*org.apache.hadoop.hbase.protobuf.generatedB\023ClusterStatusProtosH\001\240\001\001'))
# @@protoc_insertion_point(module_scope)
