#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import tests
from tests.tumblrposts import text_post, link_post, chat_post, photo_post, audio_post, video_post
from tumblr_warc_iter import TumblrWarcIter
from mock import MagicMock, patch, call
import vcr as base_vcr
import unittest
from kombu import Connection, Exchange, Queue, Producer
from sfmutils.state_store import DictHarvestStateStore
from sfmutils.harvester import HarvestResult, EXCHANGE, CODE_TOKEN_NOT_FOUND, STATUS_RUNNING, STATUS_SUCCESS
from sfmutils.warc_iter import IterItem
import threading
import shutil
import tempfile
import time
import os
from datetime import datetime, date
from tumblr_harvester import TumblrHarvester
from tumblrarc import Tumblrarc

vcr = base_vcr.VCR(
    cassette_library_dir='tests/fixtures',
    record_mode='once',
)


class TestTumblrHarvester(tests.TestCase):
    def setUp(self):
        self.working_path = tempfile.mkdtemp()
        self.harvester = TumblrHarvester(self.working_path)
        self.harvester.state_store = DictHarvestStateStore()
        self.harvester.result = HarvestResult()
        self.harvester.stop_harvest_seeds_event = threading.Event()

        self.harvester.message = {
            "id": "test:0",
            "type": "tumblr_blog_posts",
            "path": "/collections/test_collection_set/collection_id",
            "seeds": [
                {
                    "uid": "peacecorps",
                    "id": "seed1"
                }
            ],
            "credentials": {
                "api_key": tests.TUMBLR_API_KEY
            },
            "collection_set": {
                "id": "test_collection_set"
            },
            "collection": {
                "id": "test_collection"
            },
            "options": {
            }
        }

    def tearDown(self):
        if os.path.exists(self.working_path):
            shutil.rmtree(self.working_path)

    @patch("tumblr_harvester.Tumblrarc", autospec=True)
    def test_user_posts(self, mock_tumblrarc_class):
        mock_tumblrarc = MagicMock(spec=Tumblrarc)

        # Expecting all types posts. First returns 6 different posts, Second returns none.
        mock_tumblrarc.blog_posts.side_effect = [(text_post, link_post, chat_post,
                                                  photo_post, audio_post, video_post), ()]
        # Return mock_tumblrarc when instantiating a Tumblrarc.
        mock_tumblrarc_class.side_effect = [mock_tumblrarc]

        self.harvester.harvest_seeds()
        self.assertDictEqual({"tumblr posts": 6}, self.harvester.result.harvest_counter)
        mock_tumblrarc_class.assert_called_once_with(tests.TUMBLR_API_KEY)

        self.assertEqual([call('peacecorps', since_post_id=None)],
                         mock_tumblrarc.blog_posts.mock_calls)
        # Nothing added to state
        # self.assertEqual(0, len(self.harvester.state_store._state))

    @patch("tumblr_harvester.Tumblrarc", autospec=True)
    def test_incremental_search(self, mock_tumblrarc_class):
        mock_tumblrarc = MagicMock(spec=Tumblrarc)
        # ordering the posts by id desc
        mock_tumblrarc.blog_posts.side_effect = [(video_post, text_post, photo_post), ()]
        # Return mock_tumblrarc when instantiating a Tumblrarc.
        mock_tumblrarc_class.side_effect = [mock_tumblrarc]

        self.harvester.message["options"] = {
            # Incremental means that will only retrieve new results.
            "incremental": True
        }

        self.harvester.state_store.set_state("tumblr_harvester", "peacecorps.since_post_id", 147299875398)
        self.harvester.harvest_seeds()

        self.assertDictEqual({"tumblr posts": 3}, self.harvester.result.harvest_counter)
        mock_tumblrarc_class.assert_called_once_with(tests.TUMBLR_API_KEY)

        # since_id must be in the mock calls
        self.assertEqual([call('peacecorps', since_post_id=147299875398)],
                         mock_tumblrarc.blog_posts.mock_calls)
        self.assertNotEqual([call('peacecorps', since_post_id=None)],
                            mock_tumblrarc.blog_posts.mock_calls)
        # State updated
        # self.assertEqual(147341360917,
        #                  self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.since_post_id"))

    @staticmethod
    def _iter_items(items):
        # This is useful for mocking out a warc iter
        iter_items = []
        for item in items:
            iter_items.append(IterItem(None, None, None, None, item))
        return iter_items

    @patch("tumblr_harvester.TumblrWarcIter", autospec=True)
    def test_process(self, iter_class):
        mock_iter = MagicMock(spec=TumblrWarcIter)
        mock_iter.__iter__.side_effect = [
            self._iter_items([text_post, link_post, chat_post, photo_post, audio_post, video_post]).__iter__()]
        iter_class.side_effect = [mock_iter]

        # These are default harvest options
        self.harvester.incremental = False

        self.harvester.process_warc("test.warc.gz")
        iter_class.assert_called_once_with("test.warc.gz")
        self.assertEqual(6, self.harvester.result.stats_summary()["tumblr posts"])
        # State not set
        self.assertIsNone(self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.since_post_id"))

    # INFO:tumblr_harvester:147341360917 - text
    # INFO:tumblr_harvester:147333929711 - video
    # INFO:tumblr_harvester:147311989737 - photo

    @patch("tumblr_harvester.TumblrWarcIter", autospec=True)
    def test_process_incremental(self, iter_class):
        mock_iter = MagicMock(spec=TumblrWarcIter)
        mock_iter.__iter__.side_effect = [
            self._iter_items([text_post, video_post, photo_post]).__iter__()]
        iter_class.side_effect = [mock_iter]

        # These are default harvest options
        self.harvester.incremental = True
        self.harvester.state_store.set_state("tumblr_harvester", "peacecorps.since_post_id", 147333929711)

        self.harvester.process_warc("test.warc.gz")
        iter_class.assert_called_once_with("test.warc.gz")
        self.assertEqual(1, self.harvester.result.stats_summary()["tumblr posts"])
        # State updated
        self.assertEqual(147341360917,
                         self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.since_post_id"))

    @patch("tumblr_harvester.TumblrWarcIter", autospec=True)
    def test_process_first_incremental(self, iter_class):
        mock_iter = MagicMock(spec=TumblrWarcIter)
        mock_iter.__iter__.side_effect = [
            self._iter_items([text_post, video_post, photo_post]).__iter__()]
        iter_class.side_effect = [mock_iter]

        # These are default harvest options
        self.harvester.incremental = True

        self.harvester.process_warc("test.warc.gz")
        iter_class.assert_called_once_with("test.warc.gz")
        self.assertEqual(3, self.harvester.result.stats_summary()["tumblr posts"])
        # State updated
        self.assertEqual(147341360917,
                         self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.since_post_id"))

    @patch("tumblr_harvester.TumblrWarcIter", autospec=True)
    def test_process_no_new_incremental(self, iter_class):
        mock_iter = MagicMock(spec=TumblrWarcIter)
        mock_iter.__iter__.side_effect = [
            self._iter_items([text_post, video_post, photo_post]).__iter__()]
        iter_class.side_effect = [mock_iter]

        # These are default harvest options
        self.harvester.incremental = True
        self.harvester.state_store.set_state("tumblr_harvester", "peacecorps.since_post_id", 147341360917)

        self.harvester.process_warc("test.warc.gz")
        iter_class.assert_called_once_with("test.warc.gz")
        self.assertEqual(0, self.harvester.result.stats_summary()["tumblr posts"])
        # State updated
        self.assertEqual(147341360917,
                         self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.since_post_id"))


@unittest.skipIf(not tests.test_config_available, "Skipping test since test config not available.")
class TestTumblrHarvesterVCR(tests.TestCase):
    def setUp(self):
        self.working_path = tempfile.mkdtemp()
        self.harvester = TumblrHarvester(self.working_path)
        self.harvester.state_store = DictHarvestStateStore()
        self.harvester.result = HarvestResult()
        self.harvester.stop_harvest_seeds_event = threading.Event()
        self.harvester.message = {
            "id": "test:1",
            "type": "tumblr_blog_posts",
            "path": "/collections/test_collection_set/collection_id",
            "seeds": [
                {
                    "uid": "codingjester",
                    "id": "seed1"

                }
            ],
            "credentials": {
                "api_key": tests.TUMBLR_API_KEY
            },
            "collection_set": {
                "id": "test_collection_set"
            },
            "collection": {
                "id": "test_collection"
            },
            "options": {
            }
        }

    def tearDown(self):
        if os.path.exists(self.working_path):
            shutil.rmtree(self.working_path)

    @vcr.use_cassette(filter_query_parameters=['api_key'])
    def test_search_vcr(self):
        self.harvester.harvest_seeds()
        # check the total number, for new users don't how to check
        self.assertEqual(self.harvester.result.harvest_counter["tumblr posts"], 2134)
        # check the harvester status
        self.assertTrue(self.harvester.result.success)

    @vcr.use_cassette(filter_query_parameters=['api_key'])
    def test_incremental_search_vcr(self):
        self.harvester.message["options"]["incremental"] = True
        blog_name = self.harvester.message["seeds"][0]["uid"]
        self.harvester.state_store.set_state("tumblr_harvester", u"{}.since_post_id".format(blog_name), 109999716705)
        self.harvester.harvest_seeds()

        # Check harvest result
        self.assertTrue(self.harvester.result.success)
        # for check the number of get
        self.assertEqual(self.harvester.result.harvest_counter["tumblr posts"], 103)

    @vcr.use_cassette(filter_query_parameters=['api_key'])
    def test_incremental_search_corner_vcr(self):
        self.harvester.message["options"]["incremental"] = True
        blog_name = self.harvester.message["seeds"][0]["uid"]
        self.harvester.state_store.set_state("tumblr_harvester", u"{}.since_post_id".format(blog_name), 145825561465)
        self.harvester.harvest_seeds()

        # Check harvest result
        self.assertTrue(self.harvester.result.success)
        # for check the number of get
        self.assertEqual(self.harvester.result.harvest_counter["tumblr posts"], 0)
        # check the state
        self.assertEqual(145825561465,
                         self.harvester.state_store.get_state("tumblr_harvester",
                                                              u"{}.since_post_id".format(blog_name)))

    @vcr.use_cassette(filter_query_parameters=['api_key'])
    def test_harvest_invalid_blogname_vcr(self):
        self.harvester.message["seeds"] = [
            {
                "id": "seed_id1",
                "uid": "invalid_1"
            },
            {
                "id": "seed_id2",
                "uid": "invalid_2"
            }]
        self.harvester.harvest_seeds()

        self.assertEqual(2, len(self.harvester.result.warnings))
        self.assertEqual(CODE_TOKEN_NOT_FOUND, self.harvester.result.warnings[0].code)


@unittest.skipIf(not tests.test_config_available, "Skipping test since test config not available.")
@unittest.skipIf(not tests.integration_env_available, "Skipping test since integration env not available.")
class TestTumblrHarvesterIntegration(tests.TestCase):
    @staticmethod
    def _create_connection():
        return Connection(hostname="mq", userid=tests.mq_username, password=tests.mq_password)

    def setUp(self):
        self.exchange = Exchange(EXCHANGE, type="topic")
        self.result_queue = Queue(name="result_queue", routing_key="harvest.status.tumblr.*", exchange=self.exchange,
                                  durable=True)
        self.warc_created_queue = Queue(name="warc_created_queue", routing_key="warc_created", exchange=self.exchange)
        tumblr_harvester_queue = Queue(name="tumblr_harvester", exchange=self.exchange)
        with self._create_connection() as connection:
            self.result_queue(connection).declare()
            self.result_queue(connection).purge()
            self.warc_created_queue(connection).declare()
            self.warc_created_queue(connection).purge()
            # avoid raise NOT_FOUND error 404
            tumblr_harvester_queue(connection).declare()
            tumblr_harvester_queue(connection).purge()

        self.harvest_path = None

    def tearDown(self):
        if self.harvest_path:
            shutil.rmtree(self.harvest_path, ignore_errors=True)

    def test_blog_posts(self):
        self.harvest_path = "/sfm-collection-set-data/collection_set/test_collection/test_2"
        harvest_msg = {
            "id": "test:2",
            "type": "tumblr_blog_posts",
            "path": self.harvest_path,
            "seeds": [
                {
                    "uid": "gwuscrc",
                    "id": "seed1"
                }
            ],
            "credentials": {
                "api_key": tests.TUMBLR_API_KEY
            },
            "collection_set": {
                "id": "test_collection_set"
            },
            "collection": {
                "id": "test_collection"
            },
            "options": {
            }
        }
        with self._create_connection() as connection:
            bound_exchange = self.exchange(connection)
            producer = Producer(connection, exchange=bound_exchange)
            producer.publish(harvest_msg, routing_key="harvest.start.tumblr.tumblr_blog_posts")

            # Now wait for status message.
            status_msg = self._wait_for_message(self.result_queue, connection)
            # Matching ids
            self.assertEqual("test:2", status_msg["id"])
            # Running
            self.assertEqual(STATUS_RUNNING, status_msg["status"])

            # Another running message
            status_msg = self._wait_for_message(self.result_queue, connection)
            self.assertEqual(STATUS_RUNNING, status_msg["status"])

            # Now wait for result message.
            result_msg = self._wait_for_message(self.result_queue, connection)
            # Matching ids
            self.assertEqual("test:2", result_msg["id"])
            # Success
            self.assertEqual(STATUS_SUCCESS, result_msg["status"])
            # Some posts
            self.assertTrue(result_msg["stats"][date.today().isoformat()]["tumblr posts"])

            # Warc created message.
            # check path exist
            warc_msg = self._wait_for_message(self.warc_created_queue, connection)
            self.assertTrue(os.path.isfile(warc_msg["warc"]["path"]))

    def _wait_for_message(self, queue, connection):
        counter = 0
        message_obj = None
        bound_result_queue = queue(connection)
        while counter < 180 and not message_obj:
            time.sleep(.5)
            message_obj = bound_result_queue.get(no_ack=True)
            counter += 1
        self.assertIsNotNone(message_obj, "Timed out waiting for result at {}.".format(datetime.now()))
        return message_obj.payload
