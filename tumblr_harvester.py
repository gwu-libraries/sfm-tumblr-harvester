from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
import pytumblr
import time

log = logging.getLogger(__name__)

QUEUE = "tumblr_harvester"
TIMELINE_ROUTING_KEY = "harvest.start.tumblr.tumblr_user_timeline"
SEARCH_ROUTING_KEY = "harvest.start.tumblr.tumblr_search"


class TumblrHarvester(BaseHarvester):
    def __init__(self, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, debug=debug)
        self.tumblrapi = None

    def harvest_seeds(self):
        self._create_tumblrarc()

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "tumblr_user_timeline":
            self.user_timeline()
        elif harvest_type == "tumblr_search":
            self.tag_search()
        else:
            raise KeyError

    def user_timeline(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        for seed in self.message.get("seeds", []):
            self._user_post(seed.get("token"), incremental)
            if not self.harvest_result.success:
                break

    def _user_post(self, host_name, incremental):
        log.info("Harvesting user %s. Incremental is %s.", host_name, incremental)
        assert host_name
        # Get offset from state_store
        offset = self.state_store.get_state(__name__,
                                            "{}.offset".format(host_name)) if incremental else None

        max_offset = self._process_posts(self._post(host_name=host_name, offset=offset, incremental=incremental))
        log.debug("Timeline for %s offset %s returned %s posts.", host_name,
                  offset, self.harvest_result.stats_summary().get("posts"))

        # Update state store
        if incremental and max_offset:
            self.state_store.set_state(__name__, "{}.offset".format(host_name), max_offset + offset)

    def _post(self, host_name, offset, incremental):
        start_request = 0
        params = {}

        if not offset:
            offset = 0

        while True:
            if offset:
                params['offset'] = offset
            start_request += 1
            resp = self.tumblrapi.posts(host_name, **params)
            # total_posts = resp['response']['blog']['total_posts']
            posts = resp['posts']

            if len(posts) == 0:
                log.info("no new weibo post matching %s", params)
                break

            for post in posts:
                yield post

            if not incremental:
                break

            offset += len(posts)

            if start_request == 50:
                seconds = 10
                log.info("Reach max request, offset %d, sleep %d.", offset, seconds)
                time.sleep(seconds)
                # reset start request
                start_request = 0

    def _process_posts(self, posts):
        max_offset = 0
        for count, post in enumerate(posts):
            if not count % 100:
                log.debug("Processed %s posts", count)
            if self.stop_event.is_set():
                log.debug("Stopping since stop event set.")
                break
            if 'id' in post:
                self.harvest_result.increment_stats("posts")
                max_offset += 1
        return max_offset

    def tag_search(self):
        pass

    def _create_tumblrarc(self):
        self.tumblrapi = pytumblr.TumblrRestClient(self.message["credentials"]["consumer_key"],
                                                   self.message["credentials"]["consumer_secret"],
                                                   self.message["credentials"]["access_token"],
                                                   self.message["credentials"]["access_token_secret"])


if __name__ == "__main__":
    TumblrHarvester.main(TumblrHarvester, QUEUE, [TIMELINE_ROUTING_KEY, SEARCH_ROUTING_KEY])
