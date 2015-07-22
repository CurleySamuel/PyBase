from pb.Client_pb2 import Column


#  Converts a dictionary specifying ColumnFamilys -> Qualifiers into the protobuf type.
#
#    Families should look like
#    {
#        "columnFamily1": [
#            "qual1",
#            "qual2"
#        ],
#        "columnFamily2": [
#            "qual3"
#        ]
#    }
def families_to_columns(fam):
    cols = []
    for key in fam.keys():
        c = Column()
        c.family = key
        c.qualifier.extend(fam[key])
        cols.append(c)
    return cols

