#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import logging
import time
import json
import argparse
import requests
from requests_oauthlib import OAuth1Session

from twarc import get_input, catch_conn_reset, load_config, save_config, default_config_filename

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2


def main():
    """
    The tumbrlarc command line.
    """
    parser = argparse.ArgumentParser("tumbrlarc")
    parser.add_argument("--user", dest="user",
                        help="get posts matching a user's hostname")
    parser.add_argument("--last_post", dest="last_post",
                        help="the number of posts already archive in previous time")
    parser.add_argument("--log", dest="log",
                        default="tumblrarc.log", help="log file")
    parser.add_argument("--consumer_key",
                        default=None, help="Tumblr API consumer key")
    parser.add_argument("--consumer_secret",
                        default=None, help="Tumblr API consumer secret")
    parser.add_argument("--access_token",
                        default=None, help="Tumblr API access key")
    parser.add_argument("--access_token_secret",
                        default=None, help="Tumblr API access token secret")
    parser.add_argument('-c', '--config',
                        default=default_config_filename(),
                        help="Config file containing Tumblr keys and secrets")
    parser.add_argument('-p', '--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('-w', '--warnings', action='store_true',
                        help="Include warning messages in output")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    consumer_key = args.consumer_key or os.environ.get('CONSUMER_KEY')
    consumer_secret = args.consumer_secret or os.environ.get('CONSUMER_SECRET')
    access_token = args.access_token or os.environ.get('ACCESS_TOKEN')
    access_token_secret = args.access_token_secret or os.environ.get("ACCESS_TOKEN_SECRET")

    if not (consumer_key and consumer_secret and
                access_token and access_token_secret):
        credentials = load_config(args.config, args.profile)
        if credentials:
            consumer_key = credentials['consumer_key']
            consumer_secret = credentials['consumer_secret']
            access_token = credentials['access_token']
            access_token_secret = credentials['access_token_secret']
        else:
            print("Please enter Tumblr authentication credentials")
            consumer_key = get_input('consumer key: ')
            consumer_secret = get_input('consumer secret: ')
            access_token = get_input('access_token: ')
            access_token_secret = get_input('access token secret: ')
            save_keys(args.config, args.profile, consumer_key, consumer_secret,
                      access_token, access_token_secret)

    tb = Tumblrarc(consumer_key=consumer_key,
                   consumer_secret=consumer_secret,
                   access_token=access_token,
                   access_token_secret=access_token_secret)

    if args.user:
        posts = tb.blog_posts(
            args.user,
            last_post=int(args.last_post) if args.last_post else 0,
        )
    else:
        raise argparse.ArgumentTypeError(
            "must supply one of: --user")

    # iterate through the tweets and write them to stdout
    for post in posts:

        # include warnings in output only if they asked for it
        if 'id' in post or args.warnings:
            print(json.dumps(post))

        # add some info to the log
        if "id" in post:
            logging.info("archived %s", post['post_url'])
        else:
            logging.warn(json.dumps(post))


def save_keys(filename, profile, consumer_key, consumer_secret,
              access_token, access_token_secret):
    """
    :param filename: default is twarc based on the import
    :param profile:
    :param consumer_key:
    :param consumer_secret:
    :param access_token:
    :param access_token_secret:
    :return:
    """
    save_config(filename, profile,
                consumer_key, consumer_secret,
                access_token, access_token_secret)
    print("Keys saved to", filename)


def status_error(f):
    """
    A decorator to handle http response error from the API.
    refer: https://github.com/edsu/twarc/blob/master/twarc.py
    """

    def new_f(*args, **kwargs):
        errors = 0
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                errors = 0
                return resp
            elif resp.status_code == 404:
                errors += 1
                logging.warn("404:Not found url! Sleep 1s to try again...")
                if errors > 10:
                    logging.warn("Too many errors 404, stop!")
                    resp.raise_for_status()
                logging.warn("%s from request URL, sleeping 1s", resp.status_code)
                time.sleep(1)

            # deal with the response error
            elif resp.status_code >= 500:
                errors += 1
                if errors > 30:
                    logging.warn("Too many errors from Tumblr REST API Server, stop!")
                    resp.raise_for_status()
                seconds = 60 * errors
                logging.warn("%s from Tumblr REST API Server, sleeping %d", resp.status_code, seconds)
                time.sleep(seconds)
            else:
                resp.raise_for_status()

    return new_f


class Tumblrarc(object):
    """
    It's Tumblr archiving class based on Twarc. Tumblrarc allows
    search for existing posts with specify tags and look up special
    hostname's public posts.Tumblrarc doesn't handle rate limiting
    in the API since the official has no any documents on this.
    It will delay the requests every 50 times
    """

    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret):
        """
        Instantiate a Tumblrwarc instance.
        """
        self.host = "https://api.tumblr.com"
        self.max_post = 50
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self._connect()

    def blog_posts(self, hostname, incremental=False, last_post=None, type=None, format='text'):
        """
        Issues a POST request against the API
        Not sure the rate time limit for tumblr API. I delay the request for every 50 times.
        :param hostname:
        :param last_post:
        :return:
        """
        info_url = self.host + '/v2/blog/{0}/info'.format(hostname)
        # post url format
        if type is None:
            post_url = '/v2/blog/{0}/posts'.format(hostname)
        else:
            post_url = '/v2/blog/{0}/posts/{1}'.format(hostname, type)

        url = self.host + post_url
        # the request start position
        start_request = 0
        # count of request, when reach for 50 sleep for seconds
        count_request = 0
        params = {'limit': 50, 'filter': format}

        if not last_post:
            last_post = 0

        # first get the total number of the post
        resp = self.get(info_url)
        total_post = resp.json()['response']['blog']['total_posts']

        while start_request < (total_post - last_post):
            # get post as much as possible
            diff_post = total_post - last_post - start_request
            params['limit'] = self.max_post if diff_post >= self.max_post else diff_post

            params['offset'] = start_request
            resp = self.get(url, params=params)
            posts = resp.json()['response']['posts']

            if len(posts) == 0:
                logging.info("no new weibo post matching %s", params)
                break

            for post in posts:
                yield post

            if not incremental:
                break
            # update the offset
            start_request += len(posts)

            # update the count
            count_request += 1
            if count_request == 50:
                seconds = 10
                logging.info("Reach max request per time, offset %d, sleep %d.", start_request, seconds)
                time.sleep(seconds)
                count_request = 0

    @status_error
    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    @status_error
    @catch_conn_reset
    def post(self, *args, **kwargs):
        try:
            return self.client.post(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.post(*args, **kwargs)

    def _connect(self):
        logging.info("creating http session")
        self.client = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret
        )


if __name__ == "__main__":
    main()
