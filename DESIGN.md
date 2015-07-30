#HBase, An Enigma

This document aims to be a primer on what happens under the hood in a native HBase client. It's by no means comprehensive and skips over a few of the details but it should give you some insight into the blackbox. While we're on the subject of discarding culpability I should mention that I'm not in fact a HBase wizard - instead I'm just a lowly intern trying to document what I've picked up along the way.

Before we pop open the hood try to get intimate with the following terminology -

- ###RPC
  Technically a 'remote procedure call', it's become a generic term I throw around. My intended meaning is any HBase operation [Get, Put, Append, Increment, Scan, ...], etc.

- ###Client
  Entrypoint for all RPC requests. Returned to the user in `pybase.NewClient()` the user will then funnel all operations through this client (`client.get()`, `client.scan()`, etc).

- ###Region
  A region represents a range of rows in a table that exist together as a blob in HBase.

- ###Region Server (RS)
  Region Servers are physical servers in an HBase cluster that serve a given set of regions. The entire difficulty in writing an HBase client is finding which RS you should request data from.

- ###Region Client (RC)
  This is a slight misnomer but we create an instance of a Region Client class once for every Region Server. Any operations that interact with that Region Server then go through the appropriate Region Client. This way we only need to maintain a single open connection to each RS.

- ###Meta Client (MC)
  A special case of a Region Client, the MC's sole purpose in life is to maintain a connection with the HMaster (HMaster is responsible for monitoring all the RS's). We query the MC to perform meta lookups about, 1) the region the row is located in, 2) which RS is hosting that region.

- ###Zookeeper (ZK)
  Zookeeper's well, Zookeeper. Vital for internal HBase functionality we really only need to contact the quorum every now and then to get the location of the HMaster. Preemptive clients could subscribe to ZK and have appropriate callbacks to preemptively purge caches when something happens in the cluster topology but be aware that this could put a massive load of ZK (launch 1000 clients? ZK now has to serve 1000 subscribers). This client is not preemptive - the only way we know when a RS dies is when our socket to it dies.



Now that you're buddy buddy with my terminology let's give it a shot.

## Initialization

The only thing we need from a user to launch a client is the location of the ZK quorum. We then initiate a connection to ZK and query ZK for the 'meta-region-server' znode. The data will be returned in the below format (in order) -

| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 1           | Byte | Must always be \xff
| 4           | uint32, little-endian | Total length of the payload |
| ^           | Protobuf Meta(?)  | Not used |
| 4           | uint32, little-endian | Must always be 1346524486 (PBUF)
| ^           | Protobuf MetaRegionServer | Here's your data.


Once we demarshal the MetaRegionServer protobuf type we extract the host and port of the HMaster. We then create an MC instance and attach it to the Client. To create an MC instance we open a socket to the provided host:port and send a hello message that's composed as follows -

| Size (bytes)|    Type    | Meaning
|:-----------:|:-------------:|:-----:|
| 5           | Byte | Must always be HBas\x00\x50
| 4           | uint32, little-endian | Total length of the following payload |
| ^           | Protobuf ConnectionHeader  | Not used |

We're ready for queries.

## Talking to HBase

While I'm making tables I should probably specify that nearly every message we send and receive from here on will be composed as follows (last two tables that I'll make, I promise).

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


## Searching for a Row

Doing this efficiently is really the crux of an HBase client. We cache regions as we discover them but cache items can become stale quite quickly especially in a dynamic cluster. Here's the step by step.

### Step 1. Row -> Region

We use an IntervalTree to achieve an O(log n) lookup here. An interval is composed of a region's [start_key, stop_key) however because regions are distinct across tables we instead cache on a 'meta_key' which is the table and row joined by a comma - `"{},{}".format(table,row)`. If we've already seen a region whose interval overlaps a given table and row then we're all set. We reach into the cache and pull out a region_name which looks like `test,,1436819813720.e9f6b3138adae22824b91cbb17764e04.` and can be decomposed as such - `{ table: test, start_key: '', stop_key: '1436819813720', uid: 'e9f6b3138adae22824b91cbb17764e04'}`. Now that we know which region a row falls into we can move to step 2.

But what if we get a cache miss? That's what the MC is for. We'll send a GetRequest to the HMaster and it should return both the region and the RS that the region is hosted on. To be specific we send a GetRequest with `{row: meta_key, table: "hbase:meta,,1", family: {"info": []}}`. HMaster then replies with a bunch of cells full of miscellaneous data. We parse through that data, insert the new region into our cache, create RC's for any new RegionServers and return the region_name.


### Step 2. Region -> Region Client

We need a way to map multiple regions to the same instance of a RC. For this client I was lazy and used a simple dictionary with the region_name as the key and client instance as the value. It has a higher memory footprint than it should, but hey, I have deadlines.

That's it. Now we know where to send the request. But for the sake of completeness I should mention that I have a third data structure in play - a dictionary that maps a RS's host:port to a list of region_names that it serves. This is useful for several reasons but primarily so we can, 1) Check if we've already created a RC given a RS's host:port, 2) Keep track of how many known regions a given RC serves. If we're purging stale region information and discover there are no more references to an RC we can close the client to clear up resources (primarily the socket).


## Sending a Request

The previous section told us how to find who we should send the message to, now we need to send the message.

Note: Scan is a little different and I'll cover it in a separate section.

### Step 1. Construct the message

This is really just manipulating whichever protobuf library you're using to create the desired message. However you do it, the end result should be a xyzRequest object where `xyz in ['Get', 'Scan', 'Mutate']`.

Good luck - I believe in you.

### Step 2. Send the message

Before we throw the message over the wire there are a few more things we have to do in regards to packaging the message for HBase. Consult the chart in 'Talking to HBase' for specifics but really it just involves wrapping everything in a RequestHeader and putting a bunch of numbers everywhere.

Because we're not creating an asynchronous client, as soon as we send the message over the wire we sit on the socket waiting for the reply. The intention is to make the client gevent compatible so that these blocking operations yield the processor and it can go do useful work while we wait. Also on that note, if we're supporting gevent then we need to be threadsafe and lock all critical sections with mutexes (my favorite is the edge case where N threads send a message to the same RS at the same time and intercept each other's responses. Had to do some fancy trading scheme to handle that).

### Step 3. Handle the results

A RS can reply in one of four ways -
1. It can return the data in the case of a Get
2. It can return a 'processed' response in the case of a Mutate
3. It can return a remote exception.
4. It can close the socket.

Two of these makes our life very difficult - can you guess which? To address the third possibility, what kind of remote exceptions do we handle and how do we handle them?

| Exception |    How we handle it |
|:-----------:|:-------------|
| org.apache.hadoop.hbase.regionserver.NoSuchColumnFamilyException | There's not much we can do on our end to resolve this one. The user specified a nonexistent column family so we raise an exception locally letting them know. |
| java.io.IOException    | I've discovered through testing that sometimes this exception is thrown instead of the above when bad column families are provided. Don't know why but oh well. |
| org.apache.hadoop.hbase.exceptions.RegionMovedException    | If a region used to be hosted on this RS but then got moved or split, the RS will throw this exception. It means our caches are stale so we purge our caches and ask the MC for updated region information. |
| org.apache.hadoop.hbase.NotServingRegionException | This one's worrisome. It means that while a region is in fact hosted on this RS, for whatever reason it happens to be unavailable. I don't have an ideal way to handle this so currently sleep for a little bit and retry a few times. If it's still unavailable I run back to the MC and hopefully they'll give me a new RS. |


And how do we handle the fourth possibility - the socket being closed on us (or really any socket error for that matter)? We burn the MC to the ground. No really. If the socket was closed on us it was probably because the RS died, shutdown, etc. Either way it's not ready to accept requests and so we don't want anything to do with it anymore. We close the MC and purge our cache of all regions that were handled by this MC. If it's not dead and the socket died for whatever reason then the next request to come along will spawn a new instance with a new socket connection. If it is dead then the MC will point us towards the next RS that serves our desired region.

Once we get in contact with a new RS we'll send the original request again and hopefully they'll be more amenable than the last guys.

## What about Scan?

Let's just say a scan across the whole table is a sure-fire way to fill your region cache.

### Step 1. Locate the first region

Where the first region is really depends on what the user specifies. If they specify a start_key then we do the usual process of querying for the region containing the start_key. If they don't then we query for the region containing the key \x00.

Once we find the first region then we find the hosting RS and send an initial ScanRequest. They should reply with some result cells, a scanner_id and a more_results_in_region bit.

### Step 2. Keep hitting that region

If more_results_in_region is set it means (just as you'd expect) that the first ScanResponse didn't contain all the data from this region. This is where that scanner_id comes in. The Region Servers keep track of scanner states for you (including the families, filters, and whatever data has already been returned to you). Take a ScanRequest, put your scanner_id in it and keep sending it to the region until the more_results_in_region bit is False (whilst appending the resultant cells to your partial_result).

Once the bit is False you should send a final ScanRequest to the region with the 'close_scanner' bit set. The RS can then clear any preserved state on it's end.

### Step 3. Find the next region

If the user specified a stop_key then now would be the time to check if you've already touched all the appropriate regions. stop_key < region.stop_key? No need to continue, return the result. Otherwise we need to continue to the next region.

Region intervals are inclusive on the start_key and exclusive on the stop_key. The next region can thus be located by doing a meta search for the stop_key of your current region. Once you locate the next region, send the initial ScanRequest and GOTO Step 2.


## Bad things that can happen

We're trying to build a highly available system across a cluster of not-so-available machines. We may not be able to fix everything (I'm looking at you ZooKeeper) but we can at least gracefully fail when the impossible happens.

### Can't connect to Zookeeper

Pretty much SOL with this one. We can handle Zookeeper being dead as long as we know the location of HMaster and it stays alive, but that doesn't really matter as I doubt HBase will last long without Zookeeper.

Solution: Raise an exception.

### Can't connect to HMaster

We run back to Zookeeper and ask them for the new location of HMaster. Zookeeper dead? See above.

If ZooKeeper gives us bad information then we sleep and retry a few times but ultimately give up.

Solution: Raise an exception.

### Can't connect to a Region Server

As mentioned earlier, burn it to the ground and purge the relevant information in our caches. Then run back to the MC and ask it for the new region information for a given table and row. Insert the new information into our caches and create a new RC if it doesn't already exist for the RS. MC dead? See above.

Solution: We didn't need you anyway!

## Questions/Suggestions?

Shoot me an email at CurleySamuel@gmail.com. I'm friendly, I promise.
