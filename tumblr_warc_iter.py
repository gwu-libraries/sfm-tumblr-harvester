#!/usr/bin/env python

from __future__ import absolute_import
from sfmutils.warc_iter import BaseWarcIter
from dateutil.parser import parse as date_parse

class TumblrWarcIter(BaseWarcIter):
    def __init__(self, file_paths, limit_user_ids=None):
        BaseWarcIter.__init__(self, file_paths)
        self.limit_user_ids = limit_user_ids

    def _select_record(self, url):
        return url.startswith("https://api.tumblr.com/v2")

    def _item_iter(self, url, json_obj):
        # kick out the blog info archive
        if 'posts' in json_obj['response']:
            for post in json_obj['response']['posts']:
                yield "tumblr_posts", post["id"], date_parse(post["date"]), post

    @staticmethod
    def item_types():
        return ["tumblr_posts"]

    def _select_item(self, item):
        if not self.limit_user_ids or item.get("id", {}) in self.limit_user_ids:
            return True
        return False

if __name__ == "__main__":
    TumblrWarcIter.main(TumblrWarcIter)