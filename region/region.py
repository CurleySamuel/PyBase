from struct import unpack
from ..pb.HBase_pb2 import RegionInfo as pbRegionInfo


class Region:

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
            "HBase returned an invalid response (are you running a version of HBase supporting Protobufs?)")
    region_info = pbRegionInfo()
    region_info.ParseFromString(cell.value[4:-4])
    table = region_info.table_name.qualifier
    region_name = cell.row
    start_key = region_info.start_key
    stop_key = region_info.end_key
    return Region(table, region_name, start_key, stop_key)

