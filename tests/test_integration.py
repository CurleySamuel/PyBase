import unittest
import pybase
from collections import defaultdict
from time import sleep
from pybase.exceptions import *


# Please note that all below unit tests require the existence of a table
# to play with. Table must contain two column families specified below as well.
table = "test"
zkquorum = "localhost"
cf1 = "cf1"
cf2 = "cf2"


class TestClient(unittest.TestCase):

    def test_new_client_good(self):
        c = pybase.NewClient(zkquorum)
        self.assertEqual(c.zkquorum, zkquorum)
        self.assertIsNotNone(c.master_client)
        self.assertIsNotNone(c.master_client.host)

    def test_new_client_bad(self):
        try:
            c = pybase.NewClient("badzkquorum")
            self.assertEqual(1, 0)
        except ZookeeperException:
            pass

    def test_client_close(self):
        c = pybase.NewClient(zkquorum)
        c.get(table, " ")
        c.close()
        self.assertEqual(len(c.region_cache), 0)
        self.assertEqual(len(c.reverse_client_cache), 0)

    def test_client_close_then_reuse(self):
        c = pybase.NewClient(zkquorum)
        values = {
            cf1: {
                "oberyn": "is the",
            }
        }
        c.put(table, self.__class__.__name__, values)
        c.close()
        res = c.get(table, self.__class__.__name__)
        self.assertEqual(result_to_dict(res), {cf1: {"oberyn": "is the"}})


class TestGet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = pybase.NewClient(zkquorum)
        cls.values = {
            cf1: {
                "oberyn": "is the",
            },
            cf2: {
                "one": "true king"
            }
        }
        cls.c.put(table, cls.__name__, cls.values)
        cls.row_prefix = cls.__name__

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_get_entire_row(self):
        res = self.c.get(table, self.row_prefix)
        self.assertEqual(result_to_dict(res), self.values)

    def test_get_specific_cell(self):
        families = {cf1: "oberyn"}
        res = self.c.get(table, self.row_prefix, families=families)
        resd = result_to_dict(res)
        self.assertEqual(resd, {cf1: {"oberyn": "is the"}})
        self.assertNotIn(cf2, resd.keys())

    def test_get_bad_table(self):
        try:
            res = self.c.get("asdasdasd", "plsfail")
            self.assertEqual(1, 0)
        except NoSuchTableException:
            pass

    def test_get_bad_row(self):
        res = self.c.get(table, "plsfail")
        self.assertFalse(res.exists)

    def test_get_bad_column_family(self):
        families = {"hodor": "oberyn"}
        try:
            self.c.get(table, self.row_prefix, families=families)
            self.assertEqual(1, 0)
        except NoSuchColumnFamilyException:
            pass

    def test_get_bad_column_qualifier(self):
        families = {cf2: "oberyn"}
        res = self.c.get(table, self.row_prefix, families=families)
        self.assertEqual(result_to_dict(res), {})

    def test_get_with_filter(self):
        ft = pybase.filters.ColumnPrefixFilter("ob")
        res = self.c.get(table, self.row_prefix, filters=ft)
        resd = result_to_dict(res)
        self.assertDictContainsSubset(resd, self.values)
        self.assertNotIn(cf2, resd.keys())

    def test_get_with_bad_filter(self):
        ft = "badfilter"
        try:
            res = self.c.get(table, self.row_prefix, filters=ft)
            self.assertEqual(1, 0)
        except ValueError:
            pass


class TestPut(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = pybase.NewClient(zkquorum)
        cls.values = {
            cf1: {
                "oberyn": "is the",
            },
            cf2: {
                "one": "true king"
            }
        }
        cls.families = {
            cf1: ["oberyn"],
            cf2: ["one"]
        }
        cls.row_prefix = cls.__name__

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_put_single_cell(self):
        values = {
            cf1: {
                "oberyn": "is the",
            }
        }
        self.c.put(table, self.row_prefix + "1", values)
        res = self.c.get(table, self.row_prefix + "1", families=self.families)
        self.assertDictContainsSubset(result_to_dict(res), self.values)
        self.assertEqual(len(res.flatten_cells()), 1)

    def test_put_multiple_cells(self):
        self.c.put(table, self.row_prefix + "2", self.values)
        res = self.c.get(table, self.row_prefix + "2", families=self.families)
        self.assertEqual(result_to_dict(res), self.values)

    def test_put_bad_table(self):
        try:
            self.c.put("hodor", "did it work?", self.values)
            self.assertEqual(1, 0)
        except NoSuchTableException:
            pass

    def test_put_malformed_values(self):
        values = {"this": "is wrong"}
        try:
            self.c.put(table, self.row_prefix + "3", values)
            self.assertEqual(1, 0)
        except MalformedValues:
            pass

    def test_put_bad_column_family(self):
        values = {"bad_cf": {"yarr": "jabooty"}}
        try:
            self.c.put(table, self.row_prefix + "4", values)
        except NoSuchColumnFamilyException:
            pass


class TestScan(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = pybase.NewClient(zkquorum)
        cls.values = {
            cf1: {
                "oberyn": "is the",
            },
            cf2: {
                "one": "true king"
            }
        }
        cls.families = {
            cf1: ["oberyn"],
            cf2: ["one"]
        }
        cls.row_prefix = cls.__name__
        cls.pFilter = pybase.filters.PrefixFilter(cls.row_prefix)
        cls.num_ops = 100
        for x in range(cls.num_ops):
            cls.c.put(table, cls.row_prefix + str(x), cls.values)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_scan_simple(self):
        rsp = self.c.scan(table, filters=self.pFilter)
        self.assertEqual(len(rsp.flatten_cells()), 200)

    def test_scan_with_range(self):
        rsp = self.c.scan(
            table, start_key=self.row_prefix + "0", stop_key=self.row_prefix + "50", filters=self.pFilter)
        # It's not 100 because rows are compared lexicographically.
        self.assertEqual(len(rsp.flatten_cells()), 92)

    def test_scan_with_bad_range(self):
        try:
            rsp = self.c.scan(
                table, start_key="hmm", stop_key=24, filters=self.pFilter)
            self.assertEqual(1, 0)
        except TypeError:
            pass

    def test_scan_with_families(self):
        fam = {cf1: ["oberyn"]}
        rsp = self.c.scan(table, filters=self.pFilter, families=fam)
        self.assertEqual(len(rsp.flatten_cells()), 100)

    def test_scan_with_bad_column_family(self):
        fam = {"hodor": ["stillhodor"]}
        try:
            rsp = self.c.scan(table, filters=self.pFilter, families=fam)
            self.assertEqual(1, 0)
        except NoSuchColumnFamilyException:
            pass

    def test_scan_with_bad_column_qualifier(self):
        fam = {cf1: ["badqual"], cf2: ["one"]}
        rsp = self.c.scan(table, filters=self.pFilter, families=fam)
        self.assertEqual(len(rsp.flatten_cells()), 100)

    def test_scan_with_second_filter(self):
        new_filter = pybase.filters.ColumnPrefixFilter("ob")
        f_list = pybase.filters.FilterList(pybase.filters.MUST_PASS_ALL, new_filter, self.pFilter)
        rsp = self.c.scan(table, filters=f_list)
        self.assertEqual(len(rsp.flatten_cells()), 100)

    def test_scan_with_bad_filter(self):
        new_filter = "hello i am filter"
        try:
            self.c.scan(table, filters=new_filter)
            self.assertEqual(1, 0)
        except ValueError:
            pass


class TestDelete(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
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
        for x in range(5):
            cls.c.put(table, cls.row_prefix + str(x), cls.values)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_delete_entire_row(self):
        rsp = self.c.delete(table, self.row_prefix + "0", self.values)
        self.assertTrue(rsp.processed)
        rsp = self.c.get(table, self.row_prefix + "0", self.families)
        self.assertEqual(len(rsp.flatten_cells()), 0)

    def test_delete_specific_cell(self):
        value = {
            cf1: {
                "oberyn": ""
            }
        }
        rsp = self.c.delete(table, self.row_prefix + "1", value)
        self.assertTrue(rsp.processed)
        rsp = self.c.get(table, self.row_prefix + "1", self.families)
        self.assertEqual(len(rsp.flatten_cells()), 1)

    def test_delete_bad_row(self):
        rsp = self.c.delete(table, "unknownrow", self.values)
        self.assertFalse(rsp.exists)

    def test_delete_bad_column_family(self):
        value = {
            cf1: {
                "oberyn": ""
            },
            "hodor": {
                "i am hodor": ""
            }
        }
        try:
            rsp = self.c.delete(table, self.row_prefix + "2", value)
            self.assertEqual(0, 1)
        except NoSuchColumnFamilyException:
            pass

    def test_delete_bad_column_qualifier(self):
        value = {
            cf1: {
                "badqual": "",
                "oberyn": ""
            }
        }
        rsp = self.c.delete(table, self.row_prefix + "3", value)
        self.assertFalse(rsp.exists)
        rsp = self.c.get(table, self.row_prefix + "3", self.families)
        self.assertEqual(len(rsp.flatten_cells()), 1)


class TestAppend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
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
        for x in range(5):
            cls.c.put(table, cls.row_prefix + str(x), cls.values)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_append_entire_row(self):
        rsp = self.c.append(table, self.row_prefix + "0", self.values)
        rspd = result_to_dict(rsp)
        self.assertEqual(rspd[cf1], {'oberyn': 'is theis the'})
        self.assertEqual(rspd[cf2], {'one': 'true kingtrue king'})
        rsp = self.c.get(table, self.row_prefix + "0", self.families)
        rspd = result_to_dict(rsp)
        self.assertEqual(rspd[cf1], {'oberyn': 'is theis the'})
        self.assertEqual(rspd[cf2], {'one': 'true kingtrue king'})

    def test_append_specific_cell(self):
        values = {
            cf1: {
                "oberyn": " append!"
            }
        }
        rsp = self.c.append(table, self.row_prefix + "1", values)
        rspd = result_to_dict(rsp)
        self.assertEqual(rspd[cf1], {'oberyn': 'is the append!'})
        rsp = self.c.get(table, self.row_prefix + "1", self.families)
        rspd = result_to_dict(rsp)
        self.assertEqual(rspd[cf1], {'oberyn': 'is the append!'})
        self.assertEqual(rspd[cf2], {'one': 'true king'})

    def test_append_bad_row(self):
        rsp = self.c.delete(table, self.row_prefix + "2", self.values)
        rsp = self.c.append(table, self.row_prefix + "2", self.values)
        self.assertFalse(rsp.processed)
        rsp = self.c.get(table, self.row_prefix + "2")
        self.assertEqual(len(rsp.cells), 0)

    def test_append_bad_column_family(self):
        values = {
            "hodor": {
                "oberyn": "is the",
            }
        }
        try:
            rsp = self.c.append(table, self.row_prefix + "3", values)
            self.assertEqual(1, 0)
        except NoSuchColumnFamilyException:
            pass

    def test_append_bad_column_qualifier(self):
        values = {
            cf1: {
                "hodor": "hodor"
            }
        }
        rsp = self.c.delete(table, self.row_prefix + "4", values)
        rsp = self.c.append(table, self.row_prefix + "4", values)
        self.assertFalse(rsp.processed)
        rsp = self.c.get(table, self.row_prefix + "4")
        self.assertEqual(len(rsp.flatten_cells()), 2)


class TestIncrement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = pybase.NewClient(zkquorum)
        cls.families = {
            cf1: ["oberyn"],
            cf2: ["one"]
        }
        cls.start_values = {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x00",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x00"
            }
        }
        cls.inc_values = {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x08"
            }
        }
        cls.row_prefix = cls.__name__
        for x in range(6):
            cls.c.put(table, cls.row_prefix + str(x), cls.start_values)

    @classmethod
    def tearDownClass(cls):
        cls.c.close()

    def test_increment_entire_row(self):
        # TODO: Exists and processed are both false...yet they should be true?
        rsp = self.c.increment(table, self.row_prefix + "0", self.inc_values)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x08"
            }
        })
        rsp = self.c.get(table, self.row_prefix + "0", self.families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x08"
            }
        })
        rsp = self.c.increment(table, self.row_prefix + "0", self.inc_values)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\n",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x10"
            }
        })
        rsp = self.c.get(table, self.row_prefix + "0", self.families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\n",
            },
            cf2: {
                "one": "\x00\x00\x00\x00\x00\x00\x00\x10"
            }
        })

    def test_increment_specific_cell(self):
        new_values = {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05"
            }
        }
        new_families = {
            cf1: ["oberyn"]
        }
        rsp = self.c.increment(table, self.row_prefix + "1", new_values)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
            }
        })
        rsp = self.c.get(table, self.row_prefix + "1", new_families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05",
            }
        })
        rsp = self.c.increment(table, self.row_prefix + "1", new_values)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\n",
            }
        })
        rsp = self.c.get(table, self.row_prefix + "1", new_families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\n",
            }
        })

    def test_increment_bad_column_family(self):
        new_values = {
            "hodor": {
                "oberyn": "\x00\x00\x00\x00\x00\x00\x00\x05"
            }
        }
        # TODO: Throwing RuntimeError: java.io.IOException when it should be throwing
        #       column family exception.
        try:
            rsp = self.c.increment(table, self.row_prefix + "2", new_values)
            self.assertEqual(1, 0)
        except NoSuchColumnFamilyException:
            pass

    def test_increment_new_column_qualifier(self):
        new_values = {
            cf1: {
                "shodor": "\x00\x00\x00\x00\x00\x00\x00\x05"
            }
        }
        new_families = {
            cf1: ["shodor"]
        }
        rsp = self.c.delete(table, self.row_prefix + "3", new_values)
        self.assertTrue(rsp.processed)
        # So this was a fun bug to track down. The problem was that every now
        # and then the below c.get call would return an empty cell list. But
        # how is that possible? We just did an append there! Well we also just
        # did a delete. So why did c.delete -> c.append -> empty cell? Because
        # HBase doesn't actually delete data, it just sets a timestamp based
        # tombstone on a cell that says all versions older than this timestamp
        # are to be deleted (then the next major compaction will remove all
        # tombstoned cells). Why does this matter? Well the delete came in at
        # millisecond X and set a tombstone saying delete everything equal to
        # or older than X. Then less than a millisecond later the append came
        # in also at millisecond X and set a value with timestamp millisecond
        # X. The append thinks everything's dandy but when I then do a get it
        # automatically filters out tombstoned cells and wallah, empty result
        # set. Solution? Sleep for a millisecond. It should only be an issue on
        # localhost and is HBase's fault, not mine (this client's too fast for
        # it's own good!)
        sleep(0.001)
        rsp2 = self.c.increment(table, self.row_prefix + "3", new_values)
        self.assertEqual(result_to_dict(rsp2), {
            cf1: {
                "shodor": "\x00\x00\x00\x00\x00\x00\x00\x05",
            }
        })
        rsp = self.c.get(table, self.row_prefix + "3", new_families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "shodor": "\x00\x00\x00\x00\x00\x00\x00\x05",
            }
        })
        rsp = self.c.increment(table, self.row_prefix + "3", new_values)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "shodor": "\x00\x00\x00\x00\x00\x00\x00\n",
            }
        })
        rsp = self.c.get(table, self.row_prefix + "3", new_families)
        self.assertEqual(result_to_dict(rsp), {
            cf1: {
                "shodor": "\x00\x00\x00\x00\x00\x00\x00\n",
            }
        })


def result_to_dict(res):
    hodor = defaultdict(dict)
    for cell in res.flatten_cells():
        hodor[cell.family][cell.qualifier] = cell.value
    return hodor


if __name__ == '__main__':
    unittest.main()
