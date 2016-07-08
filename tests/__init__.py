import logging
import unittest
import os
import socket

try:
    from test_config import *
except ImportError:
    TUMBLR_CONSUMER_KEY = os.environ.get("TUMBLR_CONSUMER_KEY")
    TUMBLR_CONSUMER_SECRET = os.environ.get("TUMBLR_CONSUMER_SECRET")
    TUMBLR_ACCESS_TOKEN = os.environ.get("TUMBLR_ACCESS_TOKEN")
    TUMBLR_ACCESS_TOKEN_SECRET = os.environ.get("TUMBLR_ACCESS_TOKEN_SECRET")

test_config_available = True if TUMBLR_CONSUMER_KEY and TUMBLR_CONSUMER_SECRET \
                                and TUMBLR_ACCESS_TOKEN and TUMBLR_ACCESS_TOKEN_SECRET else False

mq_port_available = True
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(("mq", 5672))
except socket.error:
    mq_port_available = False

mq_username = os.environ.get("MQ_ENV_RABBITMQ_DEFAULT_USER")
mq_password = os.environ.get("MQ_ENV_RABBITMQ_DEFAULT_PASS")
integration_env_available = mq_port_available and mq_username and mq_password


class TestCase(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tumblr_harvester").setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("vcr").setLevel(logging.INFO)