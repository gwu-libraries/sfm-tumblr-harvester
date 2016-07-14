from __future__ import absolute_import
import tests
from tests.tumblrposts import text_post, link_post, chat_post, photo_post, audio_post, video_post, blog_info
from mock import MagicMock, patch, call
import vcr as base_vcr
import unittest
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
from tumblrarc import Tumblrarc

vcr = base_vcr.VCR(
    cassette_library_dir='tests/fixtures',
    record_mode='once',
)


class TestTumblrHarvester(tests.TestCase):
    def setUp(self):
        self.harvester = TumblrHarvester()
        self.harvester.state_store = DictHarvestStateStore()
        self.harvester.harvest_result = HarvestResult()
        self.harvester.stop_event = threading.Event()
        self.harvester.harvest_result_lock = threading.Lock()
        self.harvester.message = {
            "id": "test:0",
            "type": "tumblr_user_posts",
            "path": "/collections/test_collection_set/collection_id",
            "seeds": [
                {
                    "token": "peacecorps"
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
                "web_resources": True,
                "sizes": ["Large"]
            }
        }

    @patch("tumblr_harvester.Tumblrarc", autospec=True)
    def test_usrer_posts(self, mock_tumblrarc_class):
        mock_tumblrarc = MagicMock(spec=Tumblrarc)
        # seting the blog info and total posts
        mock_tumblrarc.blog_info.side_effect = [(blog_info,), ()]
        # Expecting all types posts. First returns 6 different posts, Second returns none.
        mock_tumblrarc.blog_posts.side_effect = [(text_post, link_post, chat_post,
                                                  photo_post, audio_post, video_post), ()]
        # Return mock_tumblrarc when instantiating a Tumblrarc.
        mock_tumblrarc_class.side_effect = [mock_tumblrarc]

        self.harvester.harvest_seeds()
        self.assertDictEqual({"tumblr posts": 6}, self.harvester.harvest_result.stats_summary())
        mock_tumblrarc_class.assert_called_once_with(tests.TUMBLR_CONSUMER_KEY, tests.TUMBLR_CONSUMER_SECRET,
                                                     tests.TUMBLR_ACCESS_TOKEN, tests.TUMBLR_ACCESS_TOKEN_SECRET)

        self.assertEqual([call(blogname='peacecorps', incremental=False, last_post=None)],
                         mock_tumblrarc.blog_posts.mock_calls)
        # Nothing added to state
        self.assertEqual(0, len(self.harvester.state_store._state))

    @patch("tumblr_harvester.Tumblrarc", autospec=True)
    def test_incremental_search(self, mock_tumblrarc_class):
        mock_tumblrarc = MagicMock(spec=Tumblrarc)
        mock_tumblrarc.blog_info.side_effect = [(blog_info, ), ()]
        # assuming already archive 4 posts and 2 posts left.
        mock_tumblrarc.blog_posts.side_effect = [(text_post, link_post), ()]
        # Return mock_tumblrarc when instantiating a Tumblrarc.
        mock_tumblrarc_class.side_effect = [mock_tumblrarc]

        self.harvester.message["options"] = {
            # Incremental means that will only retrieve new results.
            "incremental": True
        }

        self.harvester.state_store.set_state("tumblr_harvester", "peacecorps.last_post", 4)
        self.harvester.harvest_seeds()

        self.assertDictEqual({"tumblr posts": 2}, self.harvester.harvest_result.stats_summary())
        mock_tumblrarc_class.assert_called_once_with(tests.TUMBLR_CONSUMER_KEY, tests.TUMBLR_CONSUMER_SECRET,
                                                     tests.TUMBLR_ACCESS_TOKEN, tests.TUMBLR_ACCESS_TOKEN_SECRET)

        # since_id must be in the mock calls
        self.assertEqual([call(blogname='peacecorps', incremental=True, last_post=4)],
                         mock_tumblrarc.blog_posts.mock_calls)
        self.assertNotEqual([call(blogname='peacecorps', incremental=True, last_post=None)],
                            mock_tumblrarc.blog_posts.mock_calls)
        # State updated
        self.assertEqual(6, self.harvester.state_store.get_state("tumblr_harvester", "peacecorps.last_post"))

    def test_default_harvest_options(self):
        self.harvester.extract_web_resources = False
        self.harvester.extract_media = False

        self.harvester._process_posts([text_post, link_post, chat_post, photo_post, audio_post, video_post])
        # The default will not sending web harvest
        self.assertSetEqual(set(), self.harvester.harvest_result.urls_as_set())

    def test_harvest_options_web(self):
        self.harvester.extract_web_resources = True
        self.harvester.extract_media = False
        self.harvester._process_posts([text_post, link_post, chat_post, photo_post, audio_post, video_post])
        # Testing web resources
        self.assertSetEqual({
            'http://lehmanrl.tumblr.com/post/146996540968/theres-a-before-photo-set-for-the-practical',
            'https://www.peacecorps.gov/stories/7-reasons-peace-corps-volunteers-make-the-best-startup-workers/',
            'http://maddyandpaulinsenegal.wordpress.com/pulaar-proverbs/',
            'https://soundcloud.com/chris-flowers-8/bingo-at-jennys-school-final'
        },
            self.harvester.harvest_result.urls_as_set())

    def test_harvest_options_media(self):
        self.harvester.extract_web_resources = False
        self.harvester.extract_media = True

        self.harvester._process_posts([text_post, link_post, chat_post, photo_post, audio_post, video_post])
        # Testing photo
        self.assertSetEqual({
            'https://67.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_1280.jpg'
        },
            self.harvester.harvest_result.urls_as_set())


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
            "type": "tumblr_user_posts",
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

    @vcr.use_cassette(filter_query_parameters=['api_key', 'oauth_body_hash', 'oauth_nonce', 'oauth_timestamp',
                                               'oauth_consumer_key', 'oauth_token', 'oauth_signature'])
    def test_search_vcr(self):
        self.harvester.harvest_seeds()
        # check the total number, for new users don't how to check
        self.assertEqual(self.harvester.harvest_result.stats_summary()["tumblr posts"], 50)
        # check the harvester status
        self.assertTrue(self.harvester.harvest_result.success)

    @vcr.use_cassette(filter_query_parameters=['api_key', 'oauth_body_hash', 'oauth_nonce', 'oauth_timestamp',
                                               'oauth_consumer_key', 'oauth_token', 'oauth_signature'])
    def test_incremental_search_vcr(self):
        self.harvester.message["options"]["incremental"] = True
        blog_name = self.harvester.message["seeds"][0]["token"]
        self.harvester.state_store.set_state("tumblr_harvester", "{}.last_post".format(blog_name), 20)
        self.harvester.harvest_seeds()

        # Check harvest result
        self.assertTrue(self.harvester.harvest_result.success)
        # for check the number of get
        self.assertEqual(self.harvester.harvest_result.stats_summary()["tumblr posts"], 2114)
        # check the state
        self.assertEqual(2134,
                         self.harvester.state_store.get_state("tumblr_harvester", "{}.last_post".format(blog_name)))

    @vcr.use_cassette(filter_query_parameters=['api_key', 'oauth_body_hash', 'oauth_nonce', 'oauth_timestamp',
                                               'oauth_consumer_key', 'oauth_token', 'oauth_signature'])
    def test_default_harvest_options_vcr(self):
        self.harvester.harvest_seeds()
        # The default is none
        self.assertSetEqual(set(), self.harvester.harvest_result.urls_as_set())

    @vcr.use_cassette(filter_query_parameters=['api_key', 'oauth_body_hash', 'oauth_nonce', 'oauth_timestamp',
                                               'oauth_consumer_key', 'oauth_token', 'oauth_signature'])
    def test_harvest_options_web_vcr(self):
        self.harvester.message["options"]["web_resources"] = True
        self.harvester.harvest_seeds()

        # Testing web resources
        self.assertEqual(15, len(self.harvester.harvest_result.urls_as_set()))

    @vcr.use_cassette(filter_query_parameters=['api_key', 'oauth_body_hash', 'oauth_nonce', 'oauth_timestamp',
                                               'oauth_consumer_key', 'oauth_token', 'oauth_signature'])
    def test_harvest_options_media_vcr(self):
        self.harvester.message["options"]["web_resources"] = False
        self.harvester.message["options"]["media"] = True
        self.harvester.harvest_seeds()

        # Testing photos URLs
        self.assertEqual(53, len(self.harvester.harvest_result.urls_as_set()))


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
            "id": "test:2",
            "type": "tumblr_user_posts",
            "path": self.harvest_path,
            "seeds": [
                {
                    "token": "gwuscrc"
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
                "web_resources": True,
                "media": True
            }
        }
        with self._create_connection() as connection:
            bound_exchange = self.exchange(connection)
            producer = Producer(connection, exchange=bound_exchange)
            producer.publish(harvest_msg, routing_key="harvest.start.tumblr.tumblr_user_posts")

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
            self.assertEqual("test:2", result_msg["id"])
            # Success
            self.assertEqual("completed success", result_msg["status"])
            # Some posts
            self.assertTrue(result_msg["stats"][date.today().isoformat()]["tumblr posts"])

            # Web harvest message.
            bound_web_harvest_queue = self.web_harvest_queue(connection)
            message_obj = bound_web_harvest_queue.get(no_ack=True)
            # the default value is not harvesting web resources.
            self.assertIsNotNone(message_obj, "No web harvest message.")
            web_harvest_msg = message_obj.payload
            self.assertTrue(len(web_harvest_msg["seeds"]))

            # Warc created message.
            bound_warc_created_queue = self.warc_created_queue(connection)
            message_obj = bound_warc_created_queue.get(no_ack=True)
            self.assertIsNotNone(message_obj, "No warc created message.")
            # check path exist
            warc_msg = message_obj.payload
            self.assertTrue(os.path.isfile(warc_msg["warc"]["path"]))
