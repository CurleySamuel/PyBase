# Test file that uses the client.

import pybase

a = pybase.NewClient("localhost")
b = a._find_hosting_region_client("test", "20")
c = a._find_hosting_region_client("test", "22")

print b, c

