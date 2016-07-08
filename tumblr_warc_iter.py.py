#!/usr/bin/env python

from __future__ import absolute_import
from sfmutils.warc_iter import BaseWarcIter


class TumblrWarcIter(BaseWarcIter):
    def __init__(self, file_paths, limit_user_ids=None):
        BaseWarcIter.__init__(self, file_paths)
        self.limit_user_ids = limit_user_ids

    def _select_record(self, url):
        return url.startswith("https://api.tumblr.com/v2")

    def _item_iter(self, url, json_obj):
        pass

    @staticmethod
    def item_types():
        return ["tumblr_status"]

    def _select_item(self, item):
        pass

if __name__ == "__main__":
    TumblrWarcIter.main(TumblrWarcIter)