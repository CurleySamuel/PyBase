import unittest

# Please note that all below unit tests require the existence of a table
# to play with.

table = "test"
zkquorum = "localhost"


class TestGet(unittest.TestCase):

    def test_get_entire_row(self):
        pass

    def test_get_specific_cell(self):
        pass

    def test_get_bad_row(self):
        pass

    def test_get_bad_column_family(self):
        pass

    def test_get_bad_column_qualifier(self):
        pass

    def test_get_with_filter(self):
        pass

    def test_get_with_bad_filter(self):
        pass


class TestPut(unittest.TestCase):

    def test_put_single_cell(self):
        pass

    def test_put_multiple_cells(self):
        pass

    def test_put_bad_row(self):
        pass

    def test_put_malformed_values(self):
        pass

    def test_put_bad_column_family(self):
        pass

    def test_put_bad_column_qualifier(self):
        pass


class TestScan(unittest.TestCase):

    def test_scan_simple(self):
        pass

    def test_scan_with_range(self):
        pass

    def test_scan_with_bad_range(self):
        pass

    def test_scan_with_families(self):
        pass

    def test_scan_with_bad_column_family(self):
        pass

    def test_scan_with_bad_column_qualifier(self):
        pass

    def test_scan_with_filter(self):
        pass

    def test_scan_with_bad_filter(self):
        pass


class TestDelete(unittest.TestCase):

    def test_delete_entire_row(self):
        pass

    def test_delete_specific_cell(self):
        pass

    def test_delete_bad_row(self):
        pass

    def test_delete_bad_column_family(self):
        pass

    def test_delete_bad_column_qualifier(self):
        pass


class TestAppend(unittest.TestCase):

    def test_append_entire_row(self):
        pass

    def test_append_specific_cell(self):
        pass

    def test_append_bad_row(self):
        pass

    def test_append_bad_column_family(self):
        pass

    def test_append_bad_column_qualifier(self):
        pass


class TestIncrement(unittest.TestCase):

    def test_increment_entire_row(self):
        pass

    def test_increment_specific_cell(self):
        pass

    def test_increment_nonexistent_cell(self):
        pass

    def test_increment_bad_cell(self):
        pass

    def test_increment_bad_column_family(self):
        pass

    def test_increment_bad_column_qualifier(self):
        pass


class TestAvailability(unittest.TestCase):

    # Confirms all the necessary data is there. If this test fails then
    # something's wrong.
    def test_should_always_pass(self):
        pass

    def test_launch_new_region_servers(self):
        pass

    def test_kill_region_server(self):
        pass

    def test_kill_master_server(self):
        pass

    def test_kill_zookeeper(self):
        pass

    def test_region_server_musical_chairs(self):
        pass

