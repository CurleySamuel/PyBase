import logging
from time import sleep
logger = logging.getLogger('pybase.' + __name__)
logger.setLevel(logging.DEBUG)


# All PyBase exceptions inherit from me. Assumes unrecoverable.
class PyBaseException(Exception):

    # If any subclass hasn't redefined _handle they'll
    # use this function. Assumes the exception is
    # unrecoverable and thus the _handle method
    # just reraises the exception.
    def _handle_exception(self, main_clienti, **kwargs):
        raise self.__class_(self.message)


# Parent of any exceptions involving Zookeeper
# Usually unrecoverable so use default _handle.
class ZookeeperException(PyBaseException):
    pass


# Means we couldn't connect to ZK given a timeout.
class ZookeeperConnectionException(ZookeeperException):
    pass


# ZK doesn't hold the necessary data specifying
# location of the master server.
class ZookeeperZNodeException(ZookeeperException):
    pass


# ZK either returned strange data or data not prefaced
# with "PBUF"
class ZookeeperResponseException(ZookeeperException):
    pass


# Means an RS is dead or unreachable.
class RegionServerException(PyBaseException):

    # Pass the region if we know it, otherwise
    # do a reverse lookup using host/port.
    def __init__(self, host=None, port=None, region_client=None):
        self.host = host
        self.port = port
        self.region_client = region_client

    def _handle_exception(self, main_client, **kwargs):
        if self.region_client is None:
            concat = self.host + ":" + self.port
            self.region_client = main_client.reverse_client_cache.get(
                concat, None)
        if self.region_client is not None:
            logger.warn("Region server %s:%s refusing connections. Purging cache, sleeping, retrying.",
                        self.region_client.host, self.region_client.port)
            main_client._purge_client(self.region_client)
        sleep(1.0)


# RegionServer stopped (gracefully).
class RegionServerStoppedException(RegionServerException):
    pass


# All Master exceptions inherit from me
class MasterServerException(PyBaseException):

    def _handle_exception(self, main_client, **kwargs):
        logger.warn(
            "Encountered an exception with the Master server. Reestablishing.")
        main_client._recreate_meta_client()
        sleep(1.0)


# Master gave us funky data. Unrecoverable.
class MasterMalformedResponseException(MasterServerException):
    pass


# All region exceptions inherit from me.
class RegionException(PyBaseException):

    def _handle_exception(self, main_client, **kwargs):
        if "dest_region" in kwargs:
            main_client._purge_region(kwargs["dest_region"])
            sleep(1.0)
        else:
            raise self


# Region was moved to a different RS.
class RegionMovedException(RegionException):
    pass


# Region is unavailable for whatever reason.
class NotServingRegionException(RegionException):
    pass


# The user is looking up a table that doesn't
# exist. They're silly.
class NoSuchTableException(PyBaseException):
    pass


# The user is looking up a CF that doesn't exist,
# also silly.
class NoSuchColumnFamilyException(PyBaseException):
    pass


class MalformedFamilies(PyBaseException):
    pass


class MalformedValues(PyBaseException):
    pass

