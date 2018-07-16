#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import time
import requests
from functools import wraps
import json
import argparse
import os

# The re-try time for 404 http error
MAX_TRIES_404 = 5
# The re-try time for >500 error
MAX_TRIES_500 = 30
# Official documents say it's 20 but in real it's 50 after trials
MAX_POST_PER_PAGE = 50


def main():
    """
    The tumbrlarc command line.
    """
    parser = argparse.ArgumentParser("tumbrlarc")
    parser.add_argument("--blog", dest="blog",
                        help="get posts matching a user's blogname")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum post id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest post id to search for")
    parser.add_argument("--post_type", dest="post_type",
                        choices=["", "text", "chat", "link", "photo", "audio", "video"],
                        default="", help="search blog post type")
    parser.add_argument("--filter_type", dest="filter_type",
                        choices=["text", "html", "raw"],
                        default="html", help="search blog post type")
    parser.add_argument("--log", dest="log",
                        default="tumblrarc.log", help="log file")
    parser.add_argument("--api_key",
                        default=None, help="Tumblr API key")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    api_key = args.api_key or os.environ.get('API_KEY')

    if not api_key:
        print("Please enter Tumblr authentication credentials")
        api_key = input('API key: ')

    tb = Tumblrarc(api_key=api_key)

    if args.blog:
        posts = tb.blog_posts(
            args.blog,
            since_post_id=None if not args.since_id else int(args.since_id),
            max_post_id=None if not args.max_id else int(args.max_id),
            type=None if len(args.post_type) == 0 else args.post_type,
            format=args.filter_type
        )
    else:
        raise argparse.ArgumentTypeError(
            "must supply one of: --blog")

    # iterate through the tweets and write them to stdout
    for post in posts:

        # include warnings in output only if they asked for it
        if 'id' in post or args.warnings:
            print(json.dumps(post))

        # add some info to the log
        if "id" in post:
            logging.info("archived %s", post['post_url'])
        else:
            logging.warning(json.dumps(post))


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
            logging.warning("caught connection error: %s", e)
            self.connect()
            return f(self, *args, **kwargs)

    return new_f


def http_status_wraps(f):
    """
    A decorator to handle http response error from the API.
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
                logging.warning("404:Not found url! Sleep 1s to try again...")
                if errors > MAX_TRIES_404:
                    logging.warning("Too many errors 404, stop!")
                    resp.raise_for_status()
                logging.warning("%s from request URL, sleeping 1s", resp.status_code)
                time.sleep(1)
            # add 429 response error, not sure whether it has the rate limit value
            elif resp.status_code == 429:
                # set the default wait to 300 seconds if no rate limit info in header
                seconds = 300
                logging.warning("API rate limit exceeded: sleeping %s secs", seconds)
                time.sleep(seconds)
            # deal with the response error
            elif resp.status_code >= 500:
                errors += 1
                if errors > MAX_TRIES_500:
                    logging.warning("Too many errors from Tumblr REST API Server, stop!")
                    resp.raise_for_status()
                seconds = 60 * errors
                logging.warning("%s from Tumblr REST API Server, sleeping %d", resp.status_code, seconds)
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
    It's Tumblr archiving class. Tumblrarc allows
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
    def blog_posts(self, blogname, since_post_id=None, max_post_id=None, type=None, format='html'):
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

            if len(posts) == 0:
                logging.info("reach the end of calling for tumblr blog posts.")
                break

            start_pos, end_pos = 0, len(posts)
            if max_post_id:
                start_pos = self._lower_bound(posts, max_post_id)
            if since_post_id:
                end_pos = self._upper_bound(posts, since_post_id)

            # checks the result after filtering
            if len(posts[start_pos:end_pos]) == 0:
                logging.info("no new tumblr post matching since post %s and max post id %s", since_post_id, max_post_id)
                break

            for post in posts[start_pos:end_pos]:
                yield post

            max_post_id = post['id'] - 1

            # if the page has apply filter and found the post id, it should be the last page
            if 0 < (end_pos - start_pos) < MAX_POST_PER_PAGE:
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

    @staticmethod
    def _lower_bound(posts, max_post_id):
        """
        Finding the lower bound of the position to insert the max post id
        for i<left posts[low]['id']>max_post_id
        :param posts: the posts need to deal with
        :param max_post_id: the target post id
        :return: the position for insert the max_post_id
        """
        left, right = 0, len(posts) - 1
        while left <= right:
            mid = int((left + right) / 2)
            if posts[mid]['id'] >= max_post_id:
                left = mid + 1
            else:
                right = mid - 1
        return left

    @staticmethod
    def _upper_bound(posts, since_post_id):
        """
        Finding the upper bound of the position to insert the since post id
        for i>right posts[high]['id']<since_post_id
        :param posts: the posts need to deal with
        :param since_post_id: the target since post id
        :return: the position for insert the since_post_id
        """
        left, right = 0, len(posts) - 1
        while left <= right:
            mid = int((left + right) / 2)
            if posts[mid]['id'] > since_post_id:
                left = mid + 1
            else:
                right = mid - 1
        return left


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

    def get(self, uri, **kwargs):
        """
        Request resource by get method.
        """
        url = u"{0}{1}".format(self.api_url, uri)
        res = self.session.get(url, params=kwargs)
        return res


if __name__ == "__main__":
    main()
