# Test file that uses the client.

import pybase

a = pybase.NewClient("localhost")

b = a._find_region_client_by_key("test", "20")

print b

