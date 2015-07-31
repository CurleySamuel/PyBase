class PyBaseException(Exception):
    pass

class ZookeeperException(PyBaseException):
    pass

class MasterServerException(PyBaseException):
    pass

class RegionServerException(PyBaseException):
    pass

class MalformedResponseException(PyBaseException):
    pass

class NoSuchColumnFamilyException(PyBaseException):
    pass

class NoSuchTableException(PyBaseException):
    pass

class RegionException(PyBaseException):
    pass

class RegionMovedException(PyBaseException):
    pass

class NotServingRegionException(PyBaseException):
    pass
