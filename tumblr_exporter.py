#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sfmutils.exporter import ExportResult, BaseExporter, BaseTable
from tumblr_warc_iter import TumblrWarcIter
import logging
from dateutil.parser import parse as date_parse

log = logging.getLogger(__name__)

QUEUE = "tumblr_exporter"
USER_POSTS_ROUTING_KEY = "export.start.tumblr.tumblr_user_posts"


class TumblrStatusTable(BaseTable):
    """
    Assume rows status for Tumblr posts
    """

    def __init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids):
        BaseTable.__init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids, TumblrWarcIter)

    def _header_row(self):
        return ('created_at', 'tumblr_id', 'blog_name','post_type', 'post_slug',
                'post_summary', 'post_text', 'tags', 'tumblr_url', 'tumblr_short_url')

    def _row(self, item):
        row = [date_parse(item['date']),
               item['id'],
               item['blog_name'],
               item['type'],
               item['slug'],
               item['summary'],
               self._item_content(item),
               ', '.join([tag for tag in item['tags']]),
               item['post_url'],
               item['short_url']
               ]
        return row

    def id_field(self):
        return "tumblr_id"

    def _item_content(self, item):
        """
        To extract the main text in one item since different type has different field
        """
        if item['type'] in ['audio', 'video', 'photo']:
            return item['caption']
        elif item['type'] in ['chat', 'text']:
            return item['body']
        elif item['type'] == 'link':
            return item['excerpt']


class TumblrExporter(BaseExporter):
    def __init__(self, api_base_url, mq_config=None, warc_base_path=None):
        BaseExporter.__init__(self, api_base_url, TumblrWarcIter, TumblrStatusTable, mq_config=mq_config,
                              warc_base_path=warc_base_path)


if __name__ == "__main__":
    TumblrExporter.main(TumblrExporter, QUEUE, [USER_POSTS_ROUTING_KEY])
