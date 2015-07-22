from struct import unpack
from pb.HBase_pb2 import RegionInfo as pbRegionInfo


class RegionInfo:

    def __init__(self, table, name, start, stop):
        self.table = table
        self.region_name = name
        self.start_key = start
        self.stop_key = stop


def region_info_from_cell(cell):
    magic = unpack(">I", cell.value[:4])[0]
    # 4 bytes: PBUF
    if magic != 1346524486:
        # Either it's a corrupt message or an unsupported region info version.
        return 1 / 0  # TODO
    region_info = pbRegionInfo()
    region_info.ParseFromString(cell.value[4:-4])
    table = region_info.table_name.qualifier
    region_name = cell.row
    start_key = region_info.start_key
    stop_key = region_info.end_key
    return RegionInfo(table, region_name, start_key, stop_key)

