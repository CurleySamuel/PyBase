import logging
from time import sleep
from threading import Condition, Lock, RLock, Semaphore
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
                    if not _dynamic_sleep(self, self.region_client):
                        raise self
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
            if main_client.meta_client is None or (self.host == main_client.meta_client.host and self.port == main_client.meta_client.port):
                logger.warn(
                    "Encountered an exception with the Master server. Sleeping then reestablishing.")
                if not _dynamic_sleep(self, None):
                    raise self
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
                if not _dynamic_sleep(self, kwargs["dest_region"]):
                    raise self
                _let_all_through(self, kwargs["dest_region"])
        else:
            raise self


# Region was moved to a different RS.
class RegionMovedException(RegionException):
    pass


# Region is unavailable for whatever reason.
class NotServingRegionException(RegionException):
    pass


class RegionOpeningException(RegionException):

    def _handle_exception(self, main_client, **kwargs):
        if "dest_region" in kwargs:
            if not _dynamic_sleep(self, kwargs["dest_region"]):
                raise self
        else:
            raise self


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


_buckets = defaultdict(Semaphore)
_buckets_lock = Lock()


def _let_one_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    _buckets_lock.acquire()
    my_sem = _buckets[my_tuple]
    _buckets_lock.release()
    if my_sem.acquire(blocking=False):
        # Look at me - I'm the captain now.
        return True
        pass
    else:
        # Someone else is already handling
        # the exception. Sit here until they
        # release the semaphore.
        my_sem.acquire()
        return False


def _let_all_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    _buckets_lock.acquire()
    my_sem = _buckets[my_tuple]
    while not my_sem.acquire(blocking=False):
        my_sem.release()
        # ugh.
        # When we release a semaphore we need this
        # greenlet (if gevent is being used) to yield
        # the processor so another greenlet can grab
        # the now free semaphore.
        sleep(0)
    my_sem.release()
    _buckets_lock.release()


# We want to sleep more and more with every exception retry.
def sleep_formula(x): return (x / 1.5)**2
# [0.0, 0.44, 1.77, 4.0, 7.11, 11.11, 16.0, 21.77, 28.44, 36.0]
_exception_count = defaultdict(lambda: (0, time()))
_max_retries = 7
_max_sleep = sleep_formula(_max_retries)
_max_aggregate_sleep = reduce(
    lambda x, y: x + y, map(lambda x: sleep_formula(x), range(_max_retries)))


def _dynamic_sleep(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    retries, last_retry = _exception_count[my_tuple]
    age = time() - last_retry
    if retries >= _max_retries or age > (_max_sleep * 1.2):
        # Should we fail or was the last retry a long time ago?
        # My handwavy answer is if it's been less than half the
        # time of a max sleep since you last retried, you deserve
        # to be killed.
        #
        # Ex. _max_retries=7. That means you've slept for 40.44
        # seconds already by the time you hit retries=7. If you
        # fail again within the next 21.77/2 = 10.9 seconds I'm
        # going to end you. Otherwise we'll restart the counter.
        if age < (_max_sleep / 2.0):
            # You should die.
            return False
        _exception_count.pop(my_tuple)
        return _dynamic_sleep(exception, data)
    new_sleep = sleep_formula(retries)
    _exception_count[my_tuple] = (retries + 1, time())
    logger.info("Sleeping for {0:.2f} seconds.".format(new_sleep))
    sleep(new_sleep)
    return True

