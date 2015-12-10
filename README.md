# PyBase
Native Python HBase Client (i.e doesn't use Thrift) developed during an internship at [Flipboard](https://about.flipboard.com/).

Currently supports the following commands -

- Get
- Scan
- Put
- Append
- Increment
- Delete

Additionally supports every filter [here](/filters.py) for gets and scans.

Development has slowed down now that I'm back at school. Would love help moving forward - see the contributing section for details.

## Supported Versions

Developed on HBase >= 1.0. Theoretically compatible with any version of HBase utilizing Protobuf (0.96+) but wholly untested.

## Installation

```pip install git+git://github.com/CurleySamuel/PyBase.git```

or add following to requirements.txt

<code>git+git://github.com/hzhaofb/PyBase.git#egg=pybase</code>


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
pFilter = filters.KeyOnlyFilter(True)
rsp = client.get(table, key, families=families, filters=pFilter)
```

#### Scan with a filter
```python
pFilter = filters.KeyOnlyFilter(True)
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

## Contributing

Development has slowed down now that I'm back at school. Would love help moving forward.

- Here's a [knowledge transfer document](/DESIGN.md) to help get up to speed.
- I've created a few Github [issues](https://github.com/CurleySamuel/PyBase/issues) as a starting point.
- If you want to help out feel free to shoot me an email so we don't step on each other's toes.

## Setting up HBase

Want to try out the client locally? [mblair](https://github.com/mblair) helped write a [bash script](/setup_hbase.bash) to install + setup HBase in pseudo-distributed mode on a vagrant instance.

## License

Copyright © 2015 Samuel Curley. All rights reserved. Use of this source code is governed by the Apache License 2.0 that can be found in the [LICENSE](LICENSE) file.
