import logging
import unittest
import os
import socket

try:
    from test_config import *
except ImportError:
    TUMBLR_API_KEY = os.environ.get("TUMBLR_API_KEY")

test_config_available = True if TUMBLR_API_KEY else False

mq_port_available = True
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(("mq", 5672))
except socket.error:
    mq_port_available = False

mq_username = os.environ.get("RABBITMQ_USER")
mq_password = os.environ.get("RABBITMQ_PASSWORD")
integration_env_available = mq_port_available and mq_username and mq_password


class TestCase(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("tumblr_harvester").setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("vcr").setLevel(logging.INFO)