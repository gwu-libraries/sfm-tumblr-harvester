#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import time
import requests
from requests_oauthlib import OAuth1Session
from functools import wraps
from twarc import catch_conn_reset


def http_status_wraps(f):
    """
    A decorator to handle http response error from the API.
    refer: https://github.com/edsu/twarc/blob/master/twarc.py
    """
    @wraps(f)
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


def blogname_wraps(f):
    """
    A decorator to handle the blogname in the API calling, to make sure
    get the same data when process different type input of blogname. EX:
    codingjester, codingjester.tumblr.com and blog.johnbunting.me are the
    same blog
    """
    @wraps(f)
    def new_f(*args, **kwargs):
        # since the input might integer from the sfm-ui token and unicode staff
        # to make the fun more robust
        if len(args) > 1 and u'.' not in u'{}'.format(args[1]):
                args = list(args)
                args[1] =u'{}.tumblr.com'.format(args[1])
        return f(*args, **kwargs)
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

    @blogname_wraps
    def blog_info(self, blogname):
        """
        separate the blog info for testing convenient purpose
        :param blogname:
        :return:
        """
        info_url = u'{0}/v2/blog/{1}/info'.format(self.host, blogname)
        resp = self.get(info_url)
        return resp.json()['response']['blog']

    @blogname_wraps
    def blog_posts(self, blogname, incremental=False, last_post=None, type=None, format='text'):
        """
        Issues a POST request against the API
        Not sure the rate time limit for tumblr API. I delay the request for every 50 times.
        :param blogname:
        :param last_post:
        :return:
        """
        # post url format
        if type is None:
            post_url = u'/v2/blog/{0}/posts'.format(blogname)
        else:
            post_url = u'/v2/blog/{0}/posts/{1}'.format(blogname, type)

        url = self.host + post_url
        # the request start position
        start_request = 0
        # count of request, when reach for 50 sleep for seconds
        count_request = 0
        params = {'limit': 50, 'filter': format}

        if not last_post:
            last_post = 0

        # first get the total number of the post
        resp = self.blog_info(blogname)
        total_post = resp['total_posts']

        while start_request < (total_post - last_post):
            # get post as much as possible
            diff_post = total_post - last_post - start_request
            params['limit'] = self.max_post if diff_post >= self.max_post else diff_post

            params['offset'] = start_request
            resp = self.get(url, params=params)
            posts = resp.json()['response']['posts']

            if len(posts) == 0:
                logging.info("no new tumblr post matching %s", params)
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

    @http_status_wraps
    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    @http_status_wraps
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

