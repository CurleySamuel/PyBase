from pb.Client_pb2 import Column, MutationProto


#  Converts a dictionary specifying ColumnFamilys -> Qualifiers into the Column pb type.
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
    try:
        cols = []
        for key in fam.keys():
            c = Column()
            c.family = key
            c.qualifier.extend(fam[key])
            cols.append(c)
        return cols
    except Exception:
        raise ValueError("Malformed families")


# Converts a dictionary specifying ColumnFamilys -> Qualifiers -> Values into the protobuf type.
#
#   {
#      "cf1": {
#           "mycol": "hodor",
#           "mycol2": "alsohodor"
#      },
#      "cf2": {
#           "mycolumn7": 24
#      }
#   }
def values_to_column_values(val, delete=False):
    try:
        col_vals = []
        for cf in val.keys():
            cv = MutationProto.ColumnValue()
            cv.family = cf
            qual_vals = []
            for qual in val[cf].keys():
                qv = MutationProto.ColumnValue.QualifierValue()
                qv.qualifier = qual
                qv.value = val[cf][qual]
                if delete:
                    qv.delete_type = 1
                qual_vals.append(qv)
            cv.qualifier_value.extend(qual_vals)
            col_vals.append(cv)
        return col_vals
    except Exception:
        raise ValueError("Malformed values")

