# HBase, An Enigma

This document aims to be a primer on what happens under the hood in a native HBase client. I've split it up into three core sections - the Basic, the Advanced and the Ugly. Each section builds off the previous except addresses additional layers of complexity. Only want an overview? Hit the Basic section. Want to drown yourself in the particulars of HBase? Read all three sections and you'll be waist deep.

Before we pop open the hood I should first mention that I'm by no means an HBase wizard. Instead I'm just a lowly intern trying to document what I've picked up along the way.

Alright. Let's go.

Step 1. Get intimate with the following terminology -

- ### RPC
  Technically a remote procedure call, it's become a generic term I throw around. My intended meaning is any HBase operation [Get, Put, Append, Increment, Scan, ...], etc.

- ### Client
  Entrypoint for all operations. Returned to the user in `pybase.NewClient()` the user will then funnel all operations through this client (`client.get()`, `client.scan()`, etc).

- ### Region
  A region represents a range of rows in a table that exist together as a blob in HBase.

- ### Region Server (RS)
  Region Servers are physical servers in an HBase cluster that serve a given set of regions. The entire difficulty in writing an HBase client is finding which region in which RS you should request data from (and you know, the whole highly available thing).

- ### Region Client (RC)
  This is a slight misnomer but we create an instance of a Region Client class once for every Region Server. Any operations that interact with that Region Server then go through the appropriate Region Client. This way we only need to maintain a single open connection to each RS. If we're aware of five regions but they're all served on the same RS, we'll only have a single RC instance.

- ### Master Client (MC)
  A special case of a Region Client, the MC's sole purpose in life is to maintain a connection with the HMaster (HMaster is responsible for monitoring all the RS's). We query the MC to perform meta lookups about, 1) the region the row is located in, 2) which RS is hosting that region.

- ### Zookeeper (ZK)
  Zookeeper's well, Zookeeper. Vital for internal HBase functionality we really only need to contact the quorum every now and then to get the location of the HMaster. Preemptive clients could subscribe to ZK and have appropriate callbacks to preemptively purge caches when something happens in the cluster topology but be aware that this could put a massive load of ZK (launch 1000 clients? ZK now has to serve 1000 subscribers). This client is not preemptive - the only way we know when a RS dies is when our socket to it dies.



# The Basic

## HBase Topology

HBase is composed of three main classes of servers - Master Server, Region Server, Zookeeper nodes. When it comes to client code Zookeeper plays a minor role as we only ever use it to discover the address of the Master server. Once we know where the Master is we can close the connection. The Master tracks all region activity across all the Region Servers. If a region is split then eventually the Master will know about it. This means that if we need to know which region we should insert a key into we can ask the Master and they should return the region's details as well as the Region Server which currently hosts that region. The RegionServers are the slaves of the cluster - performing all the work while the other guys just coordinate. When we perform a get we directly contact the responsible RegionServer and ask them for the data.

<div style="text-align:center">
  <img src="http://4.bp.blogspot.com/-aO1Py3KDAp4/UUzPvUzd34I/AAAAAAAAC0Q/9I7AOvC5dx4/s1600/HBase+cluster.png" width=700>
</div>


While we're talking about general HBase knowledge I should probably mention the different between rows, column families, and columns. HBase is different from a canonical database in that you're allowed (and frankly expected) to have very sparse data spread across millions of columns. While most conventional databases tend to grow vertically as you add more and more rows against an explicit and small number of columns, HBase can grow both vertically and horizontally as columns can be created dynamically in runtime.

Here's a useful JSONified way of understanding the relationship between the three -

```python
{
  "table1": {
    "column_family_1": [
      "col1",
      "col2",
      "col3"
    ],
    "column_family_2": [
      "col1",   # distinct column from above
      "col4"
    ]
  },
  "table2": {
    "column_family_1": [  # distinct column family from above
      "col7"
    ]
  }
}
```


To create a new table there's only two things you need to initially specify - the table name and any column families you'd like. A column family can be thought of as an umbrella over columns and can be used to help prevent column qualifier collisions across the table (`cf:col1` is a different column than `cf2:col1`). While they really should be thought of as immutable, you can create and delete column families after the fact. Columns on the other hand are intended to be created as we go! When a table starts out it'll be a bunch of empty column families until the user starts adding cells (and thus creating new columns) to column qualifiers that don't yet exist.


## Initialization

When a user creates a new client instance we only really need to two things -

1. Establish a connection to ZK and request the location of the Master node.

2. Establish a connection to the Master node.

Now we're ready for requests.

## Sending a Request
##### `c.get("table", "key")`

Alright. They're looking for the contents of row 'key' on table 'table'. How do we serve this?

Seeing as our cache is cold the first step is we need to reach out to Master asking for the details on the region which hosts the given table, key. Master will respond with a few things including -

1. The unique region name and the range of keys that fall into this region.
2. The IP / Port of the RegionServer that happens to serve this region.

Now we know where to send a request but we want to cache the results so future lookups for this key can be served without having to reach out to Master again. But we can do a step better. Master returned a range of keys on this table that fall into the same region so we can actually cache the entire range of keys. Because entire ranges map to a region our cache is an IntervalTree which can return the interval that contains a given key in logarithmic time.

We send the request and the Region server should give us back a response if nothing went wrong. Now the next time we get a request for row "key" (or any row contained in the interval that the discovered region serves) we can immediately push the request to the correct RS.

And that's really all there is to it. An HBase client is just a glorified proxy with a user-facing API. The real difficulty lies in the error handling and endless edge cases which have to be covered, most of which should be covered below!

# The Advanced

This is where things start to get fun. This section and the next ("The Ugly") aim to provide a lot more detail into the heart of the client. Specifically the Advanced section will go into more depth but also cover all the error handling and failure cases. "The Ugly" will deal more with implementation detail and specifically all the work that goes on to make the client threadsafe and compatible with gevent.

## Dude, where's my row?

Figuring out where to send our message efficiently is one of the many cruxes of an HBase client. We cache regions as we discover them but cache items can become stale quite quickly especially in a dynamic cluster.


### The Cache

The data structure behind our cache is an IntervalTree. They take O(n log n) time to build, O(n) of space, but let us perform queries in O(log n) time. By query I mean, "Given a table and key, which interval (if any) contains this key?". There are a few problems with this approach -

1. The module I'm using requires explicit intervals.
  - But HBase doesn't. If a region covers the whole table then both the start_key and stop_key are `''` (empty string). If it covers the first half of the table until the key `"xyz"` then the start_key will be `''` and the stop_key will be `'xyz'`. I get around this by catching if the stop_key is `''` and changing it to `'\xff'`. Because strings are compared lexicographically, as long as a row name doesn't start with `'\xff'` then `'' -> '\xff'` should cover the whole table.
2. Tables matter too.
  - Querying for `"row7"` in table `"test"` should return a different region than querying for `"row7"` in table `"test2"`. As such we need to make our cache account for tables as well. To do so I append the table name to the start of the interval endpoints. `["row7" -> "row84"]` now becomes `["tablename,row7" -> "tablename,row84"]`. Now to fall within the interval between row7 and row84 you must specify the table you're searching at the start of your query string.
3. ...but what about bytes?
  - Nearly everything in HBase is stored as bytes. Row keys are bytes, column qualifiers are bytes, column families are bytes. But Python doesn't have an easy, native method of storing and interacting with byte arrays. Instead we store them as strings which creates the problem - does the row `"\x63\x12\xff\x55"` fall within the interval `["\x22\x34\x00\x22", "my_name_is_sam")`? I have no idea. The comparison logic is hidden away inside the IntervalTree module and it seems to agree with HBase's comparison logic but I wouldn't use this in a life-critical system (did you know a life-critical system is designed to lose less than one life per billion hours of operation?).


### The Process

Let's assume that we've already discovered a few regions and the cache is warm. Given a request for the key `hodor` in the table `westeros` we'll walk through the following process.

1. Form the key to search for.
  - `westeros,hodor`
2. Query the IntervalTree for that key.
  - If it returns a non-empty set we have a hit. GOTO 7
  - If it returns an empty set we have a cache miss.
3. Query Master for the region information.
4. Parse Master's response and create a new Region instance for this region.
5. Check if we already have a RC instance serving this RS.
  - If so, attach that instance to this region.
  - If not, establish a connection to the new RS.
6. Take our new Region and insert it into the cache.
  - Delete any overlapping intervals and purge those respective regions and RCs.
7. We have a destination.


## Sending a Request

The previous section told us how to find who we should send the message to, now we need to send the message.

Note: Scan is a little different and I'll cover it in a separate section.

### Step 1. Construct the message

This is really just manipulating whichever Protobuf library you're using to create the desired message. However you do it, the end result should be a xyzRequest object where `xyz in ['Get', 'Scan', 'Mutate']`. Good luck - I believe in you.

Filters can get a little tricky. // TODO

### Step 2. Send the message

Before we throw the message over the wire there are a few more things we have to do in regards to packaging the message for HBase. Consult the chart in 'Message Composition' for specifics but really it just involves wrapping everything in a RequestHeader and putting a bunch of integers everywhere.

### Step 3. Handle the results

A RS can reply in one of four ways -
1. It can return the data in the case of a Get.
2. It can return a 'processed' response in the case of a Mutate.
3. It can return a remote exception.
4. It can close the socket.

Two of these makes our life very difficult. In the case of a remote exception we can divide them into two categories - recoverable and unrecoverable exceptions. An example of an unrecoverable exception is where a user did a GET on a non-existent column family. An example of a recoverable exception is where the region is temporarily offline (could be because it's busy flushing it's memstore or it's in the process of being split). Depending on what type of exception was thrown we handle it differently. See the "ALL the failures!" section for details.

And how do we handle the fourth possibility - the socket being closed on us (or really any socket error for that matter)? We burn the RC to the ground. If the socket was closed on us it was probably because the RS died, shutdown, etc. Either way it's not ready to accept requests and so we don't want anything to do with it anymore. We'll throw a local exception which will close the RC and do some cache manipulation. See the exceptions section for details.


## What about Scan?

Let's just say a scan across the whole table is a sure-fire way to fill your region cache.

### Step 1. Locate the first region

Where the first region is really depends on what the user specifies. If they specify a start_key then we do the usual process of querying for the region containing the start_key. If they don't then we query for the region containing the key `""`.

Once we find the first region then we find the hosting RS and send an initial ScanRequest. They should reply with some result cells, a scanner_id and a more_results_in_region bit.

### Step 2. Keep hitting that region

If more_results_in_region is set it means (just as you'd expect) that the first ScanResponse didn't contain all the data from this region. This is where that scanner_id comes in. The Region Servers keep track of scanner states for you (including the families, filters, and whatever data has already been returned to you). Take a ScanRequest, put your scanner_id in it and keep sending it to the region until the more_results_in_region bit is False (whilst appending the intermediate cells to your partial_result).

Once the bit is False you should send a final ScanRequest to the region with the 'close_scanner' bit set. The RS can then clear any preserved state on it's end.

### Step 3. Find the next region

If the user specified a stop_key then now would be the time to check if you've already touched all the appropriate regions. `stop_key < region.stop_key`? No need to continue, return the result. Otherwise we need to continue to the next region.

Region intervals are inclusive on the start_key and exclusive on the stop_key. The next region can thus be located by doing a meta search for the stop_key of your current region. Once you locate the next region, GOTO Step 1.


## Message Composition

Up until this point I've been very hand-wavy by saying, "Now send the message!" Alas, no longer. Below is how we compose messages to the various services and nodes within HBase. Note that when I use the carrot symbol I intend that the size in bytes of this component is equal to the value of the above bytes parsed into whatever integer format they're in.


### Zookeeper
Using whatever Zookeeper client you're most comfortable with, initiate a connection to ZK and get the data stored in the 'meta-region-server' znode. The data can be parsed using the below format -

| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 1           | Byte | Must always be \xff
| 4           | uint32, little-endian | Total length of the payload |
| ^           | Protobuf Meta(?)  | Not used |
| 4           | uint32, little-endian | Must always be 1346524486 (PBUF)
| ^           | Protobuf MetaRegionServer | Here's your data.


Once we demarshal the MetaRegionServer protobuf type we extract the host and port of the HMaster. Using this information we can then...

### Master (establish connection)
To connect to Master we open a socket at the location that ZK gave us and send the following hello message. If everything is dandy then Master won't reply.

| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 5           | Byte | Must always be HBas\x00\x50
| 4           | uint32, little-endian | Total length of the following payload |
| ^           | Protobuf ConnectionHeader  | Details about connection |

Any META lookups to Master will then be a standard GET request equivalent to how you'd query a Region Server. Your query would be for region `hbase:meta,,1`, row `table,key,;`, and column family `info`.

### Region Servers

The vast majority of RPCs are to Region Servers and follow the following format.

#### Request
| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 4           | uint32, little-endian | Total length of the entire message
| 1           | Byte | Length of the following header |
| ^           | Protobuf RequestHeader  | Contains a unique id and request type |
| Variable    | varint  | Length of the following request |
| ^    | Protobuf xyzRequest  | Specific PB type of request |

#### Response
| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 4           | uint32, little-endian | Total length of the entire message
| Variable    | varint | Length of the following ResponseHeader |
| ^           | Protobuf ResponseHeader  | Contains unique id and any exceptions |
| Variable    | varint | Length of the following xyzResponse |
| ^           | Protobuf xyzResponse  | Contains response data |



## ALL the failures!

We're trying to build a highly available system across a cluster of not-so-available machines. We may not be able to fix everything but we can at least fail gracefully when the impossible happens.

But some exceptions are recoverable. Instead of having exception handling littered throughout the code I decided to use a different model where exceptions know how to handle themselves. What I mean by this is that every custom PyBase exception has a custom method `_handle_exception` which will either re-raise the exception in the case that this exception isn't recoverable or it will perform the necessary work to resolve the exception in the case of a recoverable exception. This often means purging the cache and closing clients/regions.

Below I've mapped exceptions that can be thrown either remotely on HBase or locally in the client to my custom PyBase exceptions. Further down I then list all the custom PyBase exceptions and what they do to attempt resolution.


| Exception |    PyBase Exception |
|:-----------:|:-------------|
| (RegionServer) socket.error | RegionServerException |
| (MasterServer) socket.error | MasterServerException |
| Can't connect to RS | RegionServerException |
| org.apache.hadoop.hbase.regionserver.NoSuchColumnFamilyException | NoSuchColumnFamilyException |
| java.io.IOException | NoSuchColumnFamilyException |
| org.apache.hadoop.hbase.exceptions.RegionMovedException | RegionMovedException |
| org.apache.hadoop.hbase.NotServingRegionException | NotServingRegionException |
| org.apache.hadoop.hbase.regionserver.RegionServerStoppedException | RegionServerException |
| org.apache.hadoop.hbase.exceptions.RegionOpeningException | RegionOpeningException |
| All other remote exceptions | PyBaseException |
| Cannot marshal Filter | ValueError |
| Cannot marshal Comparable | ValueError |
| Cannot marshal BytesBytesPair | ValueError |
| Cannot marshal RowRange | ValueError |
| Cannot connect to ZK | ZookeeperConnectionException |
| Cannot find ZNode in ZK | ZookeeperZNodeException |
| Malformed ZK response | ZookeeperResponseException |
| Cannot marshal Families | MalformedFamilies |
| Cannot marshal Values | MalformedValues |
| Table doesn't exist | NoSuchTableException |

| PyBase Exception | Resolution |
|:----------------:|:-----------|
| PyBaseException | Unrecoverable. Re-raise exception. |
| ZookeeperException | Unrecoverable. Re-raise exception. |
| ZookeeperConnectionException | Unrecoverable. Re-raise exception. |
| ZookeeperZNodeException | Unrecoverable. Re-raise exception. |
| ZookeeperResponseException | Unrecoverable. Re-raise exception. |
| RegionServerException | Purge both the region client and all the regions it serves from our cache. Subsequent lookups will need to reach out to rediscover the regions. |
| RegionServerStoppedException | Same as above. |
| MasterServerException | Kill the current Master client, reach out to ZK for an updated Master location, connect to new Master. |
| MasterMalformedResponseException | Unrecoverable. Re-raise exception. |
| RegionException | Purge this region from our cache. |
| RegionMovedException | Purge this region from our cache. |
| NotServingRegionException | Purge this region from our cache. |
| RegionOpeningException | Sleep. |
| NoSuchTableException | Unrecoverable. Re-raise exception. |
| NoSuchColumnFamilyException | Unrecoverable. Re-raise exception. |
| MalformedFamilies | Unrecoverable. Re-raise exception. |
| MalformedValues | Unrecoverable. Re-raise exception. |


These handling methods are all well and good but sometimes all it takes to resolve an exception is time. ZK may need to update, Master may need to update, a region may just be temporarily down. Instead of retrying instantly and hammering the server we want a way to be able to exponentially back off on our retry attempts until a final failure threshold. To do so any recoverable exception will include a call to `_dynamic_sleep` in it's handling method.

How `_dynamic_sleep` works is it buckets exceptions based on both the exception class that was raised and a special attribute that the exception aims to resolve (could be a region instance or a client instance). This way if a `RegionOpeningException` is thrown at the same time for Region1, Region2 they won't be bucketed together. If `RegionOpeningException` is thrown at the same time for the same region then they will be bucketed together.

Given these buckets that we've formed we can then keep track of how long it's been since a similar exception has been thrown. With that knowledge we can then exponentially increase the sleep time.

# The Ugly

We know how and where to send requests. We know how to handle failures and exceptions across the board. What's left to do?  

Thread safety.

For the uninitiated, gevent is a popular Python library that introduces the concept of greenlets. Greenlets can be thought of as very lightweight threads that can't be preempted but automatically yield the processor on any blocking calls or I/O. This means that while one greenlet is blocked receiving on a socket another greenlet can do useful work. A very common use case of gevent and PyBase could be -

```python
from gevent import monkey
monkey.patch_all()
import gevent
import pybase

def perform_get(key):
    c.get("test", str(key))

c = pybase.NewClient("localhost")
threads = []
for i in range(1, 1000):
    threads.append(gevent.spawn(perform_get, i))
gevent.joinall(threads)
```

What this code does is simultaneously launch 1000 GET requests through PyBase. This means that we'll have 1000 different 'threads' at different points inside our client at the same time. In it's current state the client will break and all hell would break loose.

The rest of this document is mainly implementation details and the approaches I took to make PyBase gevent compatible.

## Mutexes are your friend

First step to thread safety is surround all critical sections in mutexes (locks in Python). I ended up using 7.

- Lock on cache access.
- Lock on master requests (only want one thread to query the master at any given time).
- Write lock on every socket for every region client.
- Read lock on every socket for every region client.
- Lock on call_id (monotonically increasing RPC id).
- Lock on data structures used by threads to swap results (see below).
- Lock on the buckets used to bucket exceptions.

## HBase can respond out of order

Take the following scenario.

- Thread 1 sends a hard request to HBase, grabs the read lock on the socket and starts listening for it's results.
- Thread 2 comes in and sends an easy request to HBase then blocks trying to acquire the socket read lock.
- Easy request's response is returned on the socket to Thread 1.
- Thread 2 can now acquire the socket read lock and starts listening on the socket.
- Hard request's response is returned on the socket to Thread 2.

Uh oh. The threads got the wrong results back. To fix this I implemented the following trading algorithm -

1. If your thread's call_id matches the response's call_id, you have the correct response. Otherwise GOTO 2.
2. Insert into the `missed_rpcs` dictionary with key equal to the response's call_id and value equal to the raw response.
3. Perform a `notifyAll()` on the `missed_rpcs_condition` variable.
4. While your call_id is not in the `missed_rpcs` dictionary, wait on the condition variable.
5. Pop your call_id from the dictionary and go back to processing the results using the raw response data provided in the dictionary.

Greenlets can now trade RPCs if they happened to catch the wrong response on the socket!

## Redundant META lookups

1000 threads come in and they all get a cache miss because they all happen to be shooting for the same undiscovered region. If you're not careful you can send out 1000 META requests to the master server, all of them identical. We want to be able to send a single META lookup and have all 1000 threads use the (now cached) results of that lookup.

To implement this I surround the `_find_hosting_region` method with a `_master_lookup_lock`. Whichever thread is able to acquire the mutex first will enter the loop, perform the META lookup, discover the region/client and add everything to the cache before releasing the lock. The 999 threads which didn't come first will then re-check the cache to see if the region returned by the first thread is applicable to them or not. If so, great, they can continue. Otherwise the next person to acquire the mutex performs their own META call and so forth.

## Exception avalanche

1000 threads try to ping a Region Server but the Region Server is dead, thus 1000 exceptions are thrown. The handling method for a RegionServerException like this is to purge the RC and all it's associated regions - but we only want to do it once, not 1000 times. We can break this into two key subproblems -

1. We need a way to bucket similar exceptions.
  - We can use the same bucketing algorithm as when we were bucketing exceptions for our dynamic sleep. That is we form tuples composed from `(thrown_exception_class_name, region_or_client_instance_were_trying_to_resolve)`. Any threads that share the same tuple are then deemed to be in the same bucket. Buckets can communicate via a dictionary that uses the tuple as the key.
2. Given a bucket of exceptions we need one thread to attempt resolution while the others sit there waiting to be notified, "Hey, you can try your request again."
  - ##### `_let_one_through`

    The arguments to this function are all the necessary information to bucket a given exception. Every exception in a bucket will then share a semaphore. The function flow is then -
    - Attempt a non-blocking acquire on the semaphore.
    - If you get the semaphore then you're the effective leader of the thread.
      - The function then returns True to you and you should go on your way handling the exception. Once the exception is handled you must then call `let_all_through`.
    - If you don't get the semaphore it means some other thread is already off handling the exception and all you need to do is relax. Now perform a blocking acquire on the semaphore and once you acquire it, release it and return False.
    - Returning True/False allows the calling function to diverge execution depending on whether you're the handling thread or not.

  - ##### `_let_all_through`

    Once you've handled the exception and everything is dandy then you should call `_let_all_through` to unblock the other threads in your bucket. The flow is -

    - While a non-blocking acquire on the semaphore is False
      - Release the semaphore.
      - Yield the processor.
    - Once you can finally acquire the semaphore again it means that all other threads that were waiting on the semaphore have been let through. At this point you can return as the bucket is now empty!

# Questions/Suggestions?

Shoot me an email at CurleySamuel@gmail.com. I'm friendly, I promise.
