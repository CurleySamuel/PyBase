from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import unittest

import pybase
from pybase.exceptions import ZookeeperException

# Please note that all below unit tests require the existence of a table
# to play with. Table must contain two column families specified below as well.

table = "test"
zkquorum = "localhost"
cf1 = "cf1"
cf2 = "cf2"


class TestAvailability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        start_region_servers(["1"])
        stop_region_servers(["3", "4", "5"])
        cls.c = pybase.NewClient(zkquorum)
        cls.families = {
            cf1: ["oberyn"],
            cf2: ["one"]
        }
        cls.values = {
            cf1: {
                "oberyn": "is the",
            },
            cf2: {
                "one": "true king"
            }
        }
        cls.row_prefix = cls.__name__
        cls.num_ops = 1000
        cls.pFilter = pybase.filters.PrefixFilter(cls.row_prefix)
        for x in range(cls.num_ops):
            cls.c.put(table, cls.row_prefix + str(x), cls.values)
        start_region_servers(["2"])
        hbase_shell("balance")

    @classmethod
    def tearDownClass(cls):
        stop_region_servers(["2"])
        cls.c.close()

    # Confirms all the necessary data is there. If this test fails then
    # something's wrong.
    def test_should_always_pass(self):
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)

    def test_launch_new_region_servers(self):
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        start_region_servers(["3", "4"])
        hbase_shell("balance")
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        stop_region_servers(["3", "4"])

    def test_kill_region_server(self):
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        stop_region_servers(["2"])
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        start_region_servers(["2"])

    def test_kill_master_server(self):
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        start_region_servers(["3"])
        stop_region_servers(["1", "2"])
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        start_region_servers(["1", "2"])
        stop_region_servers(["3"])

    def test_kill_master_server_and_zookeeper(self):
        c = pybase.NewClient(zkquorum)
        rsp = c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 2000)
        c.zkquorum = "badzk"
        start_region_servers(["3"])
        stop_region_servers(["1", "2"])
        try:
            rsp = c.scan(table, filters=self.pFilter)
            self.assertEqual(1, 0)
        except ZookeeperException:
            pass
        start_region_servers(["1", "2"])
        stop_region_servers(["3"])
        c.close()

    def test_region_server_musical_chairs(self):
        pass


# Currently no admin functionality. Have to go through the hbase shell to
# do things like moving regions, rebalancing, etc.
def hbase_shell(cmd):
    echo = subprocess.Popen(
        ('echo', '"' + cmd + ';exit"'), stdout=subprocess.PIPE)
    subprocess.check_output(('hbase', 'shell'), stdin=echo.stdout)
    echo.wait()


def start_region_servers(server_ids):
    print("")
    a = [os.environ['HBASE_HOME'] + "/bin/local-regionservers.sh",
         "start", ' '.join(server_ids)]
    subprocess.call(a)


def stop_region_servers(server_ids):
    print("")
    a = [os.environ['HBASE_HOME'] + "/bin/local-regionservers.sh",
         "stop", ' '.join(server_ids)]
    subprocess.call(a)


if __name__ == '__main__':
    unittest.main()
