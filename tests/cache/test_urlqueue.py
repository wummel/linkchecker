# -*- coding: utf-8 -*-
# Copyright (C) 2017 Petr Dlouhý
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import unittest
from collections import namedtuple

from linkcheck.cache.results import ResultCache
from linkcheck.cache.urlqueue import Empty, NUM_PUTS_CLEANUP, UrlQueue

UrlData = namedtuple('UrlData', 'url cache_url aggregate has_result')
Aggregate = namedtuple('Aggregate', 'result_cache')


class TestUrlQueue(unittest.TestCase):

    def setUp(self):
        self.result_cache = ResultCache()
        self.urlqueue = UrlQueue()
        self.urldata1 = UrlData(
            url="Foo",
            cache_url="Foo",
            aggregate=Aggregate(
                result_cache=self.result_cache,
            ),
            has_result=True,
        )

    def test_max_allowed_urls_bad_value(self):
        with self.assertRaises(ValueError):
            UrlQueue(max_allowed_urls=0)
        with self.assertRaises(ValueError):
            UrlQueue(max_allowed_urls=-1)

    def test_qsize(self):
        """ Test qsize() """
        self.assertEquals(self.urlqueue.qsize(), 0)
        self.urlqueue.put(self.urldata1)
        self.assertEquals(self.urlqueue.qsize(), 1)

    def test_empty(self):
        """ Test empty() """
        self.assertEquals(self.urlqueue.empty(), True)
        self.urlqueue.put(self.urldata1)
        self.assertEquals(self.urlqueue.empty(), False)

    def test_get_empty(self):
        """ Test, that get() with empty queue throws Empty """
        with self.assertRaises(Empty):
            self.assertEquals(self.urlqueue.get(0.01), None)

    def test_get_negative_timeout(self):
        """ Test, that get() with negative timeout throws ValueError """
        with self.assertRaises(ValueError):
            self.assertEquals(self.urlqueue.get(-1), None)

    def test_put_get(self):
        """
        Test, that after put() we can get()
        the item and it can be get only once
        """
        self.urlqueue.put(self.urldata1)
        cached_item = (
            self.urldata1.aggregate.result_cache.get_result(self.urldata1)
        )
        self.assertEquals(cached_item, None)
        self.assertEquals(self.urlqueue.get(), self.urldata1)
        with self.assertRaises(Empty):
            self.assertEquals(self.urlqueue.get(0.01), None)

    def test_put_has_result_false(self):
        """
        Test, that element with has_result=False
        is put() on the end of queue
        """
        self.urlqueue.put(self.urldata1)
        urldata = UrlData(
            url="Bar",
            cache_url="Bar",
            aggregate=Aggregate(
                result_cache=self.result_cache,
            ),
            has_result=False,
        )
        self.urlqueue.put(urldata)
        self.assertEquals(self.urlqueue.get(), self.urldata1)
        self.assertEquals(self.urlqueue.get(), urldata)
        with self.assertRaises(Empty):
            self.assertEquals(self.urlqueue.get(0.01), None)

    def test_put_has_result_true(self):
        """
        Test, that element with has_result=True
        is put() on the beginning of queue
        """
        self.urlqueue.put(self.urldata1)
        urldata = UrlData(
            url="Bar",
            cache_url="Bar",
            aggregate=Aggregate(
                result_cache=self.result_cache,
            ),
            has_result=True,
        )
        self.urlqueue.put(urldata)
        self.assertEquals(self.urlqueue.get(), urldata)
        self.assertEquals(self.urlqueue.get(), self.urldata1)
        with self.assertRaises(Empty):
            self.assertEquals(self.urlqueue.get(0.01), None)

    def test_put_cache(self):
        """
        Test, that making put() on two elements with same
        cache_url adds only one element
        """
        self.urlqueue.put(self.urldata1)
        urldata = UrlData(
            url="Bar",
            cache_url="Foo",
            aggregate=Aggregate(
                result_cache=self.result_cache,
            ),
            has_result=True,
        )
        self.urlqueue.put(urldata)
        self.assertEquals(self.urlqueue.qsize(), 1)
        self.assertEquals(self.urlqueue.get(), self.urldata1)
        with self.assertRaises(Empty):
            self.assertEquals(self.urlqueue.get(0.01), None)

    def test_cleanup(self):
        """
        Test, that after adding NUM_PUTS_CLEANUP elements
        the queue is cleaned up.
        Whether the cleanup is was performed is determined,
        that element in cache is now on top of the queue.
        """
        for i in range(NUM_PUTS_CLEANUP - 1):
            self.urlqueue.put(
                UrlData(
                    url="Bar",
                    cache_url="Bar address %s" % i,
                    aggregate=Aggregate(
                        result_cache=self.result_cache,
                    ),
                    has_result=False,
                ),
            )
        self.assertEquals(self.urlqueue.qsize(), NUM_PUTS_CLEANUP - 1)
        urldata = UrlData(
            url="Bar",
            cache_url="Bar address",
            aggregate=Aggregate(
                result_cache=self.result_cache,
            ),
            has_result=False,
        )
        self.result_cache.add_result("Bar address 2", "asdf")
        self.urlqueue.put(urldata)
        self.assertEquals(self.urlqueue.qsize(), NUM_PUTS_CLEANUP)
        self.assertEquals(self.urlqueue.get().cache_url, "Bar address 2")
