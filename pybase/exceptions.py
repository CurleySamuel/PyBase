"""
   Copyright 2015 Samuel Curley

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
from collections import defaultdict
from functools import reduce
from threading import Lock, Semaphore
from time import sleep, time

from builtins import str

logger = logging.getLogger(__name__)


# All PyBase exceptions inherit from me. Assumes unrecoverable.
class PyBaseException(Exception):

    # If any subclass hasn't redefined _handle they'll
    # use this function. Assumes the exception is
    # unrecoverable and thus the _handle method
    # just reraises the exception.
    def _handle_exception(self, main_client, **kwargs):
        raise self.__class__(str(self))


# Parent of any exceptions involving Zookeeper
# Usually unrecoverable so use default _handle.
class ZookeeperException(PyBaseException):
    # Having trouble with ZooKeeper exceptions? They actually use their own
    # exception handling in zk/client.py! I know, I know. I'm the worst.
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

    def __init__(self, host=None, port=None, region_client=None):
        self.host = host.encode('utf8') if isinstance(host, str) else host
        self.port = port.encode('utf8') if isinstance(port, str) else port
        self.region_client = region_client

    def _handle_exception(self, main_client, **kwargs):
        # region_client not set? Then host/port must have been. Fetch the
        # client given the host, port
        if self.region_client is None:
            concat = self.host + b":" + self.port
            self.region_client = main_client.reverse_client_cache.get(
                concat, None)
        # Let one greenlet through per region_client (returns True otherwise
        # blocks and eventually returns False)
        if _let_one_through(self, self.region_client):
            try:
                if self.region_client is not None:
                    # We need to make sure that a different thread hasn't already
                    # reestablished to this region.
                    loc = self.region_client.host + b":" + self.region_client.port
                    if loc in main_client.reverse_client_cache:
                        # We're the first in and it's our job to kill the client.
                        # Purge it.
                        logger.warn("Region server %s:%s refusing connections. Purging cache, "
                                    "sleeping, retrying.",
                                    self.region_client.host, self.region_client.port)
                        main_client._purge_client(self.region_client)
                        # Sleep for an arbitrary amount of time. If this returns
                        # False then we've hit our max retry threshold. Die.
                        key = self.region_client.host + b":" + self.region_client.port
                        if not _dynamic_sleep(self, key):
                            raise self
            finally:
                # Notify all the other threads to wake up because we've handled the
                # exception for everyone!
                _let_all_through(self, self.region_client)


# RegionServer stopped (gracefully).
class RegionServerStoppedException(RegionServerException):
    pass


# All Master exceptions inherit from me
class MasterServerException(PyBaseException):

    def __init__(self, host, port):
        self.host = host.encode('utf8') if isinstance(host, str) else host
        self.port = port.encode('utf8') if isinstance(port, str) else port

    def _handle_exception(self, main_client, **kwargs):
        # Let one greenlet through. Others block and eventually return False.
        if _let_one_through(self, None):
            try:
                # Makes sure someone else hasn't already fixed the issue.
                if main_client.master_client is None or \
                        (self.host == main_client.master_client.host and
                         self.port == main_client.master_client.port):
                    logger.warn("Encountered an exception with the Master server. "
                                "Sleeping then reestablishing.")
                    if not _dynamic_sleep(self, None):
                        raise self
                    main_client._recreate_master_client()
            finally:
                _let_all_through(self, None)


# Master gave us funky data. Unrecoverable.
class MasterMalformedResponseException(MasterServerException):
    def _handle_exception(self, main_client, **kwargs):
        raise self.__class__(str(self))


# All region exceptions inherit from me.
class RegionException(PyBaseException):

    def _handle_exception(self, main_client, **kwargs):
        if "dest_region" in kwargs:
            rg_n = kwargs["dest_region"].region_name
            if _let_one_through(self, rg_n):
                try:
                    main_client._purge_region(kwargs["dest_region"])
                    if not _dynamic_sleep(self, rg_n):
                        raise self
                finally:
                    _let_all_through(self, rg_n)
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
            rg_n = kwargs["dest_region"].region_name
            # There's nothing to handle here. We just need to give the region
            # some time to open.
            if not _dynamic_sleep(self, rg_n):
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


# They gave us a malformed families structure.
class MalformedFamilies(PyBaseException):
    pass


# They gave us a malformed values structure.
class MalformedValues(PyBaseException):
    pass


# It starts getting a little intense below here. Why? Glad you asked.
# Reason is two fold -
#
# 1. Say 1000 greenlets all hit the same region server at the same time
# but that region server happens to be dead. Shit. 1000 exceptions were
# just thrown but we only want to handle it once because we're Mr. and
# Mrs. Efficient. How we go about doing that is we define two functions
# _let_one_through and _let_all_through. _let_one_through will instantly
# return True on the first greenlet but block for the other 999. Once the
# first greenlet handles the exception it then calls _let_all_through.
# After _let_all_through is called then _let_one_through will stop
# blocking and return False for the other 999 greenlets.
#
# 2. Say Master is down. We'll hit an exception, it'll handle it by
# reestablishing a connection to Master. But what if it's still down?
# We'll try reestablishing again. Still down? And again. Still down? And
# again. Instead of infinitely looping we need a way to measure how many
# times similar exceptions have been hit 'recently' so we can have failure
# thresholds for even recoverable exceptions. We do that via the function
# _dynamic_sleep which buckets exceptions based on a few properties and
# keeps track of when similar exceptions have been thrown. We then
# exponentially increase our sleep between exceptions until eventually a
# threshold is hit which means we should give up and fail. This both
# allows us to avoid infinite loops but also dynamically backoff on the
# exception handling (it may take Master 30 seconds to come online. We
# want to hit it at 1,3,7,15,31 instead of at 1,2,3,4,5,6,7,...,30)

# Buckets are defined by a tuple (exception_class_name, affected
# client/region). Depending on the type of exception the second value can
# change to either be a client instance or a region instance. For each
# bucket we hold a Semaphore which when set indicates that someone is
# already processing the exception for that bucket, when not set means
# you're the first and it's your job to process it.
_buckets = defaultdict(Semaphore)
# We also have an access lock on the above dictionary.
_buckets_lock = Lock()


# Read above for a description.
# TODO: Use the semaphore in reverse to prevent the race condition in
# _let_all_through.
def _let_one_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    # Grab my relevant semaphore.
    _buckets_lock.acquire()
    my_sem = _buckets[my_tuple]
    _buckets_lock.release()
    # Try to non-blocking acquire my semaphore. If I get it, woohoo! Otherwise
    # get comfy because we're sitting on the semaphore.
    if my_sem.acquire(blocking=False):
        # Look at me - I'm the captain now.
        return True
    else:
        # Someone else is already handling
        # the exception. Sit here until they
        # release the semaphore.
        my_sem.acquire()
        my_sem.release()
        return False


# Read above for a description.
def _let_all_through(exception, data):
    my_tuple = (exception.__class__.__name__, data)
    _buckets_lock.acquire()
    my_sem = _buckets[my_tuple]
    my_sem.release()
    _buckets_lock.release()


# We want to sleep more and more with every exception retry.
def sleep_formula(x):
    # [0.0, 0.44, 1.77, 4.0, 7.11, 11.11, 16.0, 21.77, 28.44, 36.0]
    return (x / 1.5)**2

_exception_count = defaultdict(lambda: (0, time()))
_max_retries = 7
_max_sleep = sleep_formula(_max_retries)
_max_aggregate_sleep = reduce(
    lambda x, y: x + y, map(lambda x: sleep_formula(x), range(_max_retries)))


# TODO: I'm not sure this function behaves as expected. Need to test further.
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
        if age < _max_sleep:
            # You should die.
            return False
        _exception_count.pop(my_tuple)
        return _dynamic_sleep(exception, data)
    new_sleep = sleep_formula(retries)
    _exception_count[my_tuple] = (retries + 1, time())
    logger.info("Sleeping for {0:.2f} seconds.".format(new_sleep))
    sleep(new_sleep)
    return True
