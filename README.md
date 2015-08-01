# PyBase
Native Python HBase Client (i.e doesn't use Thrift)

Undergoing active development with an intended stable release within a few weeks.

## Supported Versions

HBase >= 1.0

## Example Usage

#### Create a client
```python
import pybase
client = pybase.NewClient(zkquorum)
```
#### Insert a cell
```python
#   values = {
#      "cf1": {
#           "mycol": "hodor",
#           "mycol2": "alsohodor"
#      },
#      "cf2": {
#           "mycolumn7": "nothodor"
#      }
#   }
rsp = client.put(table, key, values)
```

#### Get an entire row
```python
rsp = client.get(table, key)
```

#### Get specific cells
```python
#    families = {
#        "columnFamily1": [
#            "qual1",
#            "qual2"
#        ],
#        "columnFamily2": [
#            "qual3"
#        ]
#    }
rsp = client.get(table, key, families=families)
```

#### Get specific cells with a filter
```python
from pybase import filters
pFilter = filters.NewKeyOnlyFilter(True)
rsp = client.get(table, key, families=families, filters=pFilter)
```

#### Scan with a filter
```python
pFilter = filters.NewKeyOnlyFilter(True)
rsp = client.scan(table, filters=pFilter)
```

#### Construct complex filters
```python
# Method 1
cFilter1 = filters.ColumnCountGetFilter(24)
cFilter2 = filters.ColumnRangeFilter("min", True, "max", True)
pFilter = filters.FilterList(filters.MUST_PASS_ALL, cFilter1, cFilter2)

# Method 2
pFilter = filters.FilterList(filters.MUST_PASS_ALL)
pFilter.add_filters(cFilter1, cFilter2)
```

#### Increment a cell
```python
# inc_values = {
#     cf1: {
#         "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
#     },
#     cf2: {
#         "one": "\x00\x00\x00\x00\x00\x00\x00\x08"
#     }
# }
rsp = c.increment(table, key, inc_values)
```
