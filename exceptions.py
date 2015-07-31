class ZookeeperException(RuntimeError):
    pass

class MasterServerException(RuntimeError):
    pass

class RegionServerException(RuntimeError):
    pass

class MalformedResponseException(RegionServerException):
    pass

class NoSuchColumnFamilyException(LookupError):
    pass

class NoSuchTableException(LookupError):
    pass
    
class RegionException(LookupError):
    pass

class RegionMovedException(RegionException):
    pass

class NotServingRegionException(RegionException):
    pass
