#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import time
import requests
from functools import wraps

# The re-try time for 404 http error
MAX_TRIES_404 = 10
# The re-try time for >500 error
MAX_TRIES_500 = 30
# Official documents say it's 20 but in real it's 50 after trials
MAX_POST_PER_PAGE = 50


def conn_reset_wraps(f):
    """
    A decorator to handle connection reset errors
    """
    try:
        import OpenSSL
        ConnectionError = OpenSSL.SSL.SysCallError
    except:
        ConnectionError = requests.exceptions.ConnectionError

    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except ConnectionError as e:
            logging.warn("caught connection error: %s", e)
            self.connect()
            return f(self, *args, **kwargs)

    return new_f


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
                if errors > MAX_TRIES_404:
                    logging.warn("Too many errors 404, stop!")
                    resp.raise_for_status()
                logging.warn("%s from request URL, sleeping 1s", resp.status_code)
                time.sleep(1)

            # deal with the response error
            elif resp.status_code >= 500:
                errors += 1
                if errors > MAX_TRIES_500:
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
            args[1] = u'{}.tumblr.com'.format(args[1])
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

    def __init__(self, api_key):
        """
        Instantiate a Tumblrwarc instance.
        """
        self.api_key = api_key
        self._connect()

    @blogname_wraps
    def blog_posts(self, blogname, since_post_id=None, max_post_id=None, type=None, format='text'):
        """
        Issues a POST request against the API
        Not sure the rate time limit for tumblr API. I delay the request for every 50 times.
        :param blogname: the blog identifier for a tumblr user
        :param since_post_id: it will return the post id larger than the id
        :param max_post_id: it will return the post id smaller than the id
        :param type: the post type to return, if none, return all types
        :param format: the content format in the return JSON results
        :return: a yield for the filter posts
        """
        # post url format
        if type is None:
            post_url = u'{0}/posts'.format(blogname)
        else:
            post_url = u'{0}/posts/{1}'.format(blogname, type)

        # the request start position
        start_request = 0
        params = {'limit': MAX_POST_PER_PAGE, 'filter': format}

        while True:
            params['offset'] = start_request
            resp = self.get(post_url, **params)
            posts = resp.json()['response']['posts']

            if max_post_id:
                posts = filter(lambda x: x['id'] < max_post_id, posts)
            if since_post_id:
                posts = filter(lambda x: x['id'] > since_post_id, posts)

            if len(posts) == 0:
                logging.info("no new tumblr post matching since post %s and max post id %s", since_post_id, max_post_id)
                break

            for post in posts:
                yield post

            max_post_id = post['id'] - 1

            # if the page has apply filter and find the last post id, it should be the last page
            if 0 < len(posts) < MAX_POST_PER_PAGE:
                logging.info("reach the last page for since post %s and max post id %s", since_post_id, max_post_id)
                break

            # go to the next page
            start_request += MAX_POST_PER_PAGE

    @http_status_wraps
    @conn_reset_wraps
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    def _connect(self):
        logging.info("creating http session")
        self.client = Client(api_key=self.api_key)


class APIError(StandardError):
    """
    raise APIError if got failed message from the API not the http error.
    """

    def __init__(self, error_code, error, request):
        self.error_code = error_code
        self.error = error
        self.request = request
        StandardError.__init__(self, error)

    def __str__(self):
        return 'APIError: %s, %s, Request: %s' % (self.error_code, self.error, self.request)


class Client(object):
    """
    Using request to instead of httplib2 since lots of works done
    to try the proxy, but in vain
    """

    def __init__(self, api_key):
        # const define
        self.site = 'https://api.tumblr.com/'
        self.api_url = self.site + 'v2/blog/'
        self.api_key = api_key
        self.session = requests.session()
        self.session.params = {'api_key': api_key}

    def _assert_error(self, d):
        """
        Assert if json response is error.
        """
        if 'error_code' in d and 'error' in d:
            raise APIError(d.get('error_code'), d.get('error', ''), d.get('request', ''))

    def get(self, uri, **kwargs):
        """
        Request resource by get method.
        """
        url = u"{0}{1}".format(self.api_url, uri)
        res = self.session.get(url, params=kwargs)
        self._assert_error(res.json())
        return res
