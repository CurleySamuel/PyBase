import logging
from time import sleep
from threading import Condition, Lock, RLock
from time import time
from collections import defaultdict
logger = logging.getLogger('pybase.' + __name__)
logger.setLevel(logging.DEBUG)


# All PyBase exceptions inherit from me. Assumes unrecoverable.
class PyBaseException(Exception):

    # If any subclass hasn't redefined _handle they'll
    # use this function. Assumes the exception is
    # unrecoverable and thus the _handle method
    # just reraises the exception.
    def _handle_exception(self, main_client, **kwargs):
        raise self.__class__(self.message)


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
        if _let_one_through(self, self.region_client):
            if self.region_client is not None:
                # We need to make sure that a different thread hasn't already
                # reestablished to this region.
                loc = self.region_client.host + ":" + self.region_client.port
                if loc in main_client.reverse_client_cache:
                    logger.warn("Region server %s:%s refusing connections. Purging cache, sleeping, retrying.",
                                self.region_client.host, self.region_client.port)
                    main_client._purge_client(self.region_client)
                    _dynamic_sleep(self, self.region_client)
            _let_all_through(self, self.region_client)


# RegionServer stopped (gracefully).
class RegionServerStoppedException(RegionServerException):
    pass


# All Master exceptions inherit from me
class MasterServerException(PyBaseException):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _handle_exception(self, main_client, **kwargs):
        if _let_one_through(self, None):
            if self.host == main_client.meta_client.host and self.port == main_client.meta_client.port:
                logger.warn(
                    "Encountered an exception with the Master server. Sleeping then reestablishing.")
                _dynamic_sleep(self, None)
                main_client._recreate_meta_client()
                _let_all_through(self, None)


# Master gave us funky data. Unrecoverable.
class MasterMalformedResponseException(MasterServerException):
    pass


# All region exceptions inherit from me.
class RegionException(PyBaseException):

    def _handle_exception(self, main_client, **kwargs):
        if "dest_region" in kwargs:
            if _let_one_through(self, kwargs["dest_region"]):
                main_client._purge_region(kwargs["dest_region"])
                _dynamic_sleep(self, kwargs["dest_region"])
                _let_all_through(self, kwargs["dest_region"])
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


# Say 10 greenlets hit the same exception. We only
# want one greenlet to make progress resolving it
# while all the others just sit there sleeping.
# When the exception is resolved, notify everyone
# to wake up.
#
# We bucket exceptions via a dictionary where the
# key is a tuple formed of (exception_class, XYZ)
# where XYZ is some exception specific data
# (usually a region or region client instance)
_buckets = {}
_buckets_lock = RLock()


def _let_one_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    with _buckets_lock:
        if my_tuple in _buckets:
            # Someone else has hit our exception already.
            # They're the master and already trying to
            # resolve the exception.
            cond = _buckets[my_tuple]
            while my_tuple in _buckets:
                cond.wait()
            return False
        else:
            # Look at me - I'm the captain now.
            _buckets[my_tuple] = Condition(_buckets_lock)
            return True

def _let_all_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    cond = _buckets.pop(my_tuple)
    cond.acquire()
    cond.notifyAll()
    cond.release()


# We want to sleep more and more with every exception retry.
# If we've passed a timeout period, fail the query.
_exception_count = defaultdict(lambda: (0, int(time())))
_max_sleep = 30


def _dynamic_sleep(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    retries, last_retry = _exception_count[my_tuple]
    # Previous exceptions could be here! Should we use them
    # or are they old?
    if (int(time()) - last_retry) > _max_sleep:
        # Old!
        _exception_count.pop(my_tuple)
        return _dynamic_sleep(exception, data)
    new_sleep = (retries / 1.5)**2
    # [0.0, 0.44, 1.77, 4.0, 7.11, 11.11, 16.0, 21.77, 28.44, 36.0]
    _exception_count[my_tuple] = (retries + 1, int(time()))
    logger.info("Sleeping for {0:.2f} seconds.".format(new_sleep))
    sleep(new_sleep)

