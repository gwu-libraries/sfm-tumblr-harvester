from __future__ import absolute_import
import tests
import vcr as base_vcr
from tests.tumblr import post1,post2
import unittest
from mock import MagicMock, patch, call
from kombu import Connection, Exchange, Queue, Producer
from sfmutils.state_store import DictHarvestStateStore
from sfmutils.harvester import HarvestResult, EXCHANGE
import threading
import shutil
import tempfile
import time
import os
from datetime import datetime, date
from tumblr_harvester import TumblrHarvester

vcr = base_vcr.VCR(
    cassette_library_dir='tests/fixtures',
    record_mode='once',
)


@unittest.skipIf(not tests.test_config_available, "Skipping test since test config not available.")
class TestTumblrHarvesterVCR(tests.TestCase):
    def setUp(self):
        self.harvester = TumblrHarvester()
        self.harvester.state_store = DictHarvestStateStore()
        self.harvester.harvest_result = HarvestResult()
        self.harvester.stop_event = threading.Event()
        self.harvester.harvest_result_lock = threading.Lock()
        self.harvester.message = {
            "id": "test:1",
            "type": "tumblr_user_timeline",
            "path": "/collections/test_collection_set/collection_id",
            "seeds": [
                {
                    "token": "codingjester"
                }
            ],
            "credentials": {
                "consumer_key": tests.TUMBLR_CONSUMER_KEY,
                "consumer_secret": tests.TUMBLR_CONSUMER_SECRET,
                "access_token": tests.TUMBLR_ACCESS_TOKEN,
                "access_token_secret": tests.TUMBLR_ACCESS_TOKEN_SECRET
            },
            "collection_set": {
                "id": "test_collection_set"
            },
            "options": {
            }
        }

    @vcr.use_cassette(filter_query_parameters=['api_key','oauth_body_hash','oauth_nonce','oauth_timestamp',
                                               'oauth_consumer_key','oauth_token','oauth_signature'])
    def test_search_vcr(self):
        self.harvester.harvest_seeds()
        # check the total number, for new users don't how to check
        self.assertEqual(self.harvester.harvest_result.stats_summary()["posts"], 20)
        # check the harvester status
        self.assertTrue(self.harvester.harvest_result.success)

    @vcr.use_cassette(filter_query_parameters=['api_key','oauth_body_hash','oauth_nonce','oauth_timestamp',
                                               'oauth_consumer_key','oauth_token','oauth_signature'])
    def test_incremental_search_vcr(self):
        self.harvester.message["options"]["incremental"] = True
        host_name = self.harvester.message["seeds"][0]["token"]
        self.harvester.state_store.set_state("tumblr_harvester", "{}.offset".format(host_name), 20)
        self.harvester.harvest_seeds()

        # Check harvest result
        self.assertTrue(self.harvester.harvest_result.success)
        # for check the number of get
        self.assertEqual(self.harvester.harvest_result.stats_summary()["posts"], 2114)
        # check the state
        self.assertEqual(2134, self.harvester.state_store.get_state("tumblr_harvester", "{}.offset".format(host_name)))


@unittest.skipIf(not tests.test_config_available, "Skipping test since test config not available.")
@unittest.skipIf(not tests.integration_env_available, "Skipping test since integration env not available.")
class TestTumblrHarvesterIntegration(tests.TestCase):
    def _create_connection(self):
        return Connection(hostname="mq", userid=tests.mq_username, password=tests.mq_password)

    def setUp(self):
        self.exchange = Exchange(EXCHANGE, type="topic")
        self.result_queue = Queue(name="result_queue", routing_key="harvest.status.tumblr.*", exchange=self.exchange,
                                  durable=True)
        self.web_harvest_queue = Queue(name="web_harvest_queue", routing_key="harvest.start.web",
                                       exchange=self.exchange)
        self.warc_created_queue = Queue(name="warc_created_queue", routing_key="warc_created", exchange=self.exchange)
        tumblr_harvester_queue = Queue(name="tumblr_harvester", exchange=self.exchange)
        with self._create_connection() as connection:
            self.result_queue(connection).declare()
            self.result_queue(connection).purge()
            self.web_harvest_queue(connection).declare()
            self.web_harvest_queue(connection).purge()
            self.warc_created_queue(connection).declare()
            self.warc_created_queue(connection).purge()
            # avoid raise NOT_FOUND error 404
            tumblr_harvester_queue(connection).declare()
            tumblr_harvester_queue(connection).purge()

        self.harvest_path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.harvest_path, ignore_errors=True)

    def test_search(self):
        harvest_msg = {
            "id": "test:1",
            "type": "tumblr_user_timeline",
            "path": self.harvest_path,
            "seeds": [
                {
                    "token": "codingjester"
                }
            ],
            "credentials": {
                "consumer_key": tests.TUMBLR_CONSUMER_KEY,
                "consumer_secret": tests.TUMBLR_CONSUMER_SECRET,
                "access_token": tests.TUMBLR_ACCESS_TOKEN,
                "access_token_secret": tests.TUMBLR_ACCESS_TOKEN_SECRET
            },
            "collection_set": {
                "id": "test_collection_set"
            },
            "options": {
            }
        }
        with self._create_connection() as connection:
            bound_exchange = self.exchange(connection)
            producer = Producer(connection, exchange=bound_exchange)
            producer.publish(harvest_msg, routing_key="harvest.start.tumblr.tumblr_user_timeline")

            # Now wait for result message.
            counter = 0
            bound_result_queue = self.result_queue(connection)
            message_obj = None
            while counter < 240 and not message_obj:
                time.sleep(.5)
                message_obj = bound_result_queue.get(no_ack=True)
                counter += 1
            self.assertTrue(message_obj, "Timed out waiting for result at {}.".format(datetime.now()))

            result_msg = message_obj.payload
            # Matching ids
            self.assertEqual("test:1", result_msg["id"])
            # Success
            self.assertEqual("completed success", result_msg["status"])
            # Some posts
            self.assertTrue(result_msg["stats"][date.today().isoformat()]["posts"])

            # Web harvest message.
            bound_web_harvest_queue = self.web_harvest_queue(connection)
            message_obj = bound_web_harvest_queue.get(no_ack=True)
            # the default value is not harvesting web resources.
            self.assertIsNotNone(message_obj, "No web harvest message.")
            web_harvest_msg = message_obj.payload
            # Some seeds
            self.assertTrue(len(web_harvest_msg["seeds"]))

            # Warc created message.
            bound_warc_created_queue = self.warc_created_queue(connection)
            message_obj = bound_warc_created_queue.get(no_ack=True)
            self.assertIsNotNone(message_obj, "No warc created message.")
            # check path exist
            warc_msg = message_obj.payload
            self.assertTrue(os.path.isfile(warc_msg["warc"]["path"]))