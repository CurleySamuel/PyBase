# Test file that uses the client.

import pybase

a = pybase.NewClient("localhost")
b = a._find_hosting_region_client("test2", "20")
b = a._find_hosting_region_client("test2", "19")
b = a._find_hosting_region_client("test2", "21")
b = a._find_hosting_region_client("test2", "4535345")
b = a._find_hosting_region_client("test2", "123")
b = a._find_hosting_region_client("test2", "545")
b = a._find_hosting_region_client("test2", "20")
c = a._find_hosting_region_client("test", "22")

a.put("test", "20", {"cf": {"a": "New Value!"}})
a.delete("test", "99", {"cf": {"a": "does it matter what I put here?"}})
a.app("test", "20", {"cf": {"a": "hello I am dog"}})

