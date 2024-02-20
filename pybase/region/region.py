"""
   Copyright 2015 Samuel Curley

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from __future__ import absolute_import, print_function, unicode_literals

from struct import unpack

from ..pb.HBase_pb2 import RegionInfo as pbRegionInfo


class Region(object):

    def __init__(self, table, name, start, stop):
        self.table = table
        self.region_name = name
        self.start_key = start
        self.stop_key = stop
        self.region_client = None

    def __repr__(self):
        return str({
            "table": self.table,
            "region_name": self.region_name,
            "start_key": self.start_key,
            "stop_key": self.stop_key,
            "region_client": self.region_client
        })


def region_from_cell(cell):
    magic = unpack(">I", cell.value[:4])[0]
    # 4 bytes: PBUF
    if magic != 1346524486:
        # Either it's a corrupt message or an unsupported region info version.
        raise RuntimeError(
            "HBase returned an invalid response (are you running a version of HBase supporting "
            "Protobufs?)")
    region_info = pbRegionInfo()
    region_info.ParseFromString(cell.value[4:-4])
    table = region_info.table_name.qualifier
    region_name = cell.row
    start_key = region_info.start_key
    stop_key = region_info.end_key
    return Region(table, region_name, start_key, stop_key)
