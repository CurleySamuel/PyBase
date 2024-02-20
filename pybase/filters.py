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

import traceback

from .pb import Comparator_pb2 as pbComparator
from .pb import Filter_pb2 as pbFilter
from .pb.HBase_pb2 import BytesBytesPair as pbBytesBytesPair

# You're brave to venture into this file.

filter_path = "org.apache.hadoop.hbase.filter."
comparator_path = "org.apache.hadoop.hbase.filter."

# Operators
MUST_PASS_ALL = 1
MUST_PASS_ONE = 2

# BitwiseOps
AND = 1
OR = 2
XOR = 3

# CompareTypes
LESS = 0
LESS_OR_EQUAL = 1
EQUAL = 2
NOT_EQUAL = 3
GREATER_OR_EQUAL = 4
GREATER = 5
NO_OP = 6


# A FilterList is also a Filter. But it's also a list of Filters with an
# operator. This allows you to build up complicated boolean expressions by
# chaining FilterLists.
class FilterList(object):

    def __init__(self, operator, *arg):
        self.filter_type = pbFilter.FilterList
        self.name = filter_path + "FilterList"
        self.operator = operator
        self.filters = []
        self.add_filters(*arg)

    def add_filters(self, *arg):
        for new_filter in arg:
            self.filters.append(_to_filter(new_filter))


class ColumnCountGetFilter(object):

    def __init__(self, limit):
        self.filter_type = pbFilter.ColumnCountGetFilter
        self.name = filter_path + "ColumnCountGetFilter"
        self.limit = limit


class ColumnPaginationFilter(object):

    def __init__(self, limit, offset, column_offset):
        self.filter_type = pbFilter.ColumnPaginationFilter
        self.name = filter_path + "ColumnPaginationFilter"
        self.limit = limit
        self.offset = offset
        self.column_offset = column_offset


class ColumnPrefixFilter(object):

    def __init__(self, prefix):
        self.filter_type = pbFilter.ColumnPrefixFilter
        self.name = filter_path + "ColumnPrefixFilter"
        self.prefix = prefix


class ColumnRangeFilter(object):

    def __init__(self, min_column, min_column_inclusive, max_column, max_column_inclusive):
        self.filter_type = pbFilter.ColumnRangeFilter
        self.name = filter_path + "ColumnRangeFilter"
        self.min_column = min_column
        self.min_column_inclusive = min_column_inclusive
        self.max_column = max_column
        self.max_column_inclusive = max_column_inclusive


class CompareFilter(object):

    def __init__(self, compare_op, comparator):
        self.filter_type = pbFilter.CompareFilter
        self.name = filter_path + "CompareFilter"
        self.compare_op = compare_op
        self.comparator = _to_comparator(comparator)


class DependentColumnFilter(object):

    def __init__(self, compare_filter, column_family, column_qualifier, drop_dependent_column):
        self.filter_type = pbFilter.DependentColumnFilter
        self.name = filter_path + "DependentColumnFilter"
        self.compare_filter = _to_filter(compare_filter)
        self.column_family = column_family
        self.column_qualifier = column_qualifier
        self.drop_dependent_column = drop_dependent_column


class FamilyFilter(object):

    def __init__(self, compare_filter):
        self.filter_type = pbFilter.FamilyFilter
        self.name = filter_path + "FamilyFilter"
        self.compare_filter = _to_filter(compare_filter)


class FilterWrapper(object):

    def __init__(self, new_filter):
        self.filter_type = pbFilter.FilterWrapper
        self.name = filter_path + "FilterWrapper"
        self.filter = _to_filter(new_filter)


class FirstKeyOnlyFilter(object):

    def __init__(self):
        self.filter_type = pbFilter.FirstKeyOnlyFilter
        self.name = filter_path + "FirstKeyOnlyFilter"


class FirstKeyValueMatchingQualifiersFilter(object):

    def __init__(self, qualifiers):
        self.filter_type = pbFilter.FirstKeyValueMatchingQualifiersFilter
        self.name = filter_path + "FirstKeyValueMatchingQualifiersFilter"
        self.qualifiers = qualifiers


class FuzzyRowFilter(object):

    def __init__(self, fuzzy_keys_data):
        self.filter_type = pbFilter.FuzzyRowFilter
        self.name = filter_path + "FuzzyRowFilter"
        self.fuzzy_keys_data = []
        try:
            for fuzz in fuzzy_keys_data:
                self.fuzzy_keys_data.append(_to_bytes_bytes_pair(fuzz))
        except TypeError:
            # They passed a single element and not a sequence of elements.
            self.fuzzy_keys_data.append(_to_bytes_bytes_pair(fuzzy_keys_data))


class InclusiveStopFilter(object):

    def __init__(self, stop_row_key):
        self.filter_type = pbFilter.InclusiveStopFilter
        self.name = filter_path + "InclusiveStopFilter"
        self.stop_row_key = stop_row_key


class KeyOnlyFilter(object):

    def __init__(self, len_as_val):
        self.filter_type = pbFilter.KeyOnlyFilter
        self.name = filter_path + "KeyOnlyFilter"
        self.len_as_val = len_as_val


class MultipleColumnPrefixFilter(object):

    def __init__(self, sorted_prefixes):
        self.filter_type = pbFilter.MultipleColumnPrefixFilter
        self.name = filter_path + "MultipleColumnPrefixFilter"
        if isinstance(sorted_prefixes, list):
            self.sorted_prefixes = sorted_prefixes
        else:
            self.sorted_prefixes = [sorted_prefixes]


class PageFilter(object):

    def __init__(self, page_size):
        self.filter_type = pbFilter.PageFilter
        self.name = filter_path + "PageFilter"
        self.page_size = page_size


class PrefixFilter(object):

    def __init__(self, prefix):
        self.filter_type = pbFilter.PrefixFilter
        self.name = filter_path + "PrefixFilter"
        self.prefix = prefix


class QualifierFilter(object):

    def __init__(self, compare_filter):
        self.filter_type = pbFilter.QualifierFilter
        self.name = filter_path + "QualifierFilter"
        self.compare_filter = _to_pb_filter(compare_filter)


class RandomRowFilter(object):

    def __init__(self, chance):
        self.filter_type = pbFilter.RandomRowFilter
        self.name = filter_path + "RandomRowFilter"
        self.chance = chance


class RowFilter(object):

    def __init__(self, compare_filter):
        self.filter_type = pbFilter.RowFilter
        self.name = filter_path + "RowFilter"
        self.compare_filter = _to_filter(compare_filter)


class SkipColumnValueExcludeFilter(object):

    def __init__(self, single_column_value_filter):
        self.filter_type = pbFilter.SkipColumnValueExcludeFilter
        self.name = filter_path + "SkipColumnValueExcludeFilter"
        self.single_column_value_filter = _to_filter(
            single_column_value_filter)


class SkipColumnValueFilter(object):

    def __init__(self, compare_op, comparator, column_family, column_qualifier, filter_if_missing,
                 latest_version_only):
        self.filter_type = pbFilter.SkipColumnValueFilter
        self.name = filter_path + "SkipColumnValueFilter"
        self.compare_op = compare_op
        self.comparator = _to_comparator(comparator)
        self.column_family = column_family
        self.column_qualifier = column_qualifier
        self.filter_if_missing = filter_if_missing
        self.latest_version_only = latest_version_only


class SkipFilter(object):

    def __init__(self, orig_filter):
        self.filter_type = pbFilter.SkipFilter
        self.name = filter_path + "SkipFilter"
        self.filter = orig_filter


class TimestampsFilter(object):

    def __init__(self, timestamps):
        self.filter_type = pbFilter.TimestampsFilter
        self.name = filter_path + "TimestampsFilter"
        if isinstance(timestamps, list):
            self.timestamps = timestamps
        else:
            self.timestamps = [timestamps]


class ValueFilter(object):

    def __init__(self, compare_filter):
        self.filter_type = pbFilter.ValueFilter
        self.name = filter_path + "ValueFilter"
        self.compare_filter = _to_filter(compare_filter)


class WhileMatchFilter(object):

    def __init__(self, origFilter):
        self.filter_type = pbFilter.WhileMatchFilter
        self.name = filter_path + "WhileMatchFilter"
        self.filter = _to_filter(origFilter)


class FilterAllFilter(object):

    def __init__(self):
        self.filter_type = pbFilter.FilterAllFilter
        self.name = filter_path + "FilterAllFilter"


class MultiRowRangeFilter(object):

    def __init__(self, row_range_list):
        self.filter_type = pbFilter.MultiRowRangeFilter
        self.name = filter_path + "MultiRowRangeFilter"
        self.row_range_list = []
        try:
            for row in row_range_list:
                self.row_range_list.append(_to_row_range(row))
        except TypeError:
            # They passed a single element and not a sequence of elements.
            self.row_range_list.append(_to_row_range(row_range_list))


# Instead of having to define a _to_filter method for every filter I
# instead opted to be hard core and define it once and support every
# filter.
#
# _to_filter will take any of the above classes, create the associated pb
# type, iterate over any special variables and set them accordingly,
# serialize the special pb filter type into a standard pb Filter object
# and return that.
def _to_filter(orig_filter):
    if orig_filter is None:
        return None
    ft = pbFilter.Filter()
    ft.name = orig_filter.name
    ft.serialized_filter = _to_pb_filter(orig_filter).SerializeToString()
    return ft


def _to_pb_filter(orig_filter):
    try:
        ft2 = orig_filter.filter_type()
        members = [
            attr for attr in dir(orig_filter)
            if not callable(attr) and not attr.startswith("__") and
            attr not in ["name", "filter_type", "add_filters"]]
        for member in members:
            try:
                val = getattr(orig_filter, member)
                if val is not None:
                    # skip none value that should be optional
                    setattr(ft2, member, val)
            except AttributeError:
                # It's a repeated element and we need to 'extend' it.
                el = getattr(ft2, member)
                try:
                    el.extend(getattr(orig_filter, member))
                except AttributeError:
                    # Just kidding. It's a composite field.
                    el.CopyFrom(getattr(orig_filter, member))
        return ft2
    except Exception as ex:
        raise ValueError("Malformed Filter provided, %s %s" % (ex, traceback.format_exc()))


class ByteArrayComparable(object):

    def __init__(self, value):
        self.comparable_type = pbComparator.ByteArrayComparable
        self.value = value


# Just like _to_filter, but for comparables.
def _to_comparable(orig_cmp):
    try:
        new_cmp = orig_cmp.comparable_type()
        members = [attr for attr in dir(orig_cmp) if not callable(
            attr) and not attr.startswith("__") and attr not in ["name", "comparable_type"]]
        for member in members:
            val = getattr(orig_cmp, member)
            # skip none value that should be optional
            if val is not None:
                setattr(new_cmp, member, val)
        return new_cmp
    except Exception as ex:
        raise ValueError("Malformed Comparable provided %s %s" % (ex, traceback.format_exc()))


class BinaryComparator(object):

    def __init__(self, comparable):
        self.comparator_type = pbComparator.BinaryComparator
        self.name = comparator_path + "BinaryComparator"
        self.comparable = _to_comparable(comparable)


class LongComparator(object):

    def __init__(self, comparable):
        self.comparator_type = pbComparator.LongComparator
        self.name = comparator_path + "LongComparator"
        self.comparable = _to_comparable(comparable)


class BinaryPrefixComparator(object):

    def __init__(self, comparable):
        self.comparator_type = pbComparator.BinaryPrefixComparator
        self.name = comparator_path + "BinaryPrefixComparator"
        self.comparable = _to_comparable(comparable)


class BitComparator(object):

    def __init__(self, comparable, bitwise_op):
        self.comparator_type = pbComparator.BitComparator
        self.name = comparator_path + "BitComparator"
        self.comparable = _to_comparable(comparable)
        self.bitwise_op = bitwise_op


class NullComparator(object):

    def __init__(self):
        self.comparator_type = pbComparator.NullComparator
        self.name = comparator_path + "NullComparator"


class RegexStringComparator(object):

    def __init__(self, pattern, pattern_flags, charset, engine):
        self.comparator_type = pbComparator.RegexStringComparator
        self.name = comparator_path + "RegexStringComparator"
        self.pattern = pattern
        self.pattern_flags = pattern_flags
        self.charset = charset
        self.engine = engine


class StringComparator(object):

    def __init__(self, substr):
        self.comparator_type = pbComparator.BinaryPrefixComparator
        self.name = comparator_path + "BinaryPrefixComparator"
        self.substr = substr


# Just like _to_filter, but for comparators.
def _to_comparator(orig_cmp):
    try:
        new_cmp = pbComparator.Comparator()
        new_cmp.name = orig_cmp.name
        new_cmp2 = orig_cmp.comparator_type()
        members = [attr for attr in dir(orig_cmp) if not callable(
            attr) and not attr.startswith("__") and attr not in ["name", "comparator_type"]]
        for member in members:
            try:
                val = getattr(orig_cmp, member)
                if val is not None:
                    # skip none value that should be optional
                    setattr(new_cmp2, member, val)
            except AttributeError:
                # It's a composite element and we need to copy it in.
                el = getattr(new_cmp2, member)
                el.CopyFrom(getattr(orig_cmp, member))
        new_cmp.serialized_comparator = new_cmp2.SerializeToString()
        return new_cmp
    except Exception as ex:
        raise ValueError("Malformed Comparator provided %s %s" % (ex, traceback.format_exc()))


class BytesBytesPair(object):

    def __init__(self, first, second):
        self.first = first
        self.second = second


def _to_bytes_bytes_pair(bbp):
    try:
        new_bbp = pbBytesBytesPair()
        new_bbp.first = bbp.first
        new_bbp.second = bbp.second
        return new_bbp
    except Exception:
        raise ValueError("Malformed BytesBytesPair provided")


class RowRange(object):

    def __init__(self, start_row, start_row_inclusive, stop_row, stop_row_inclusive):
        self.filter_type = pbFilter.RowRange
        self.name = filter_path + "RowRange"
        self.start_row = start_row
        self.start_row_inclusive = start_row_inclusive
        self.stop_row = stop_row
        self.stop_row_inclusive = stop_row_inclusive


def _to_row_range(rr):
    try:
        new = pbFilter.RowRange()
        new.start_row = rr.start_row
        new.start_row_inclusive = rr.start_row_inclusive
        new.stop_row = rr.stop_row
        new.stop_row_inclusive = rr.stop_row_inclusive
        return new
    except Exception:
        raise ValueError("Malformed RowRange provided")
