from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
from tumblrarc import Tumblrarc
import time

log = logging.getLogger(__name__)

QUEUE = "tumblr_harvester"
USER_POSTS_ROUTING_KEY = "harvest.start.tumblr.tumblr_user_posts"


class TumblrHarvester(BaseHarvester):
    def __init__(self, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, debug=debug)
        self.tumblrapi = None
        self.extract_web_resources = False
        self.extract_media = False

    def harvest_seeds(self):
        self._create_tumblrarc()

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "tumblr_user_posts":
            self.user_posts()
        else:
            raise KeyError

    def user_posts(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        # Get harvest extract options.
        self.extract_web_resources = self.message.get("options", {}).get("web_resources", False)
        self.extract_media = self.message.get("options", {}).get("media", False)

        for seed in self.message.get("seeds", []):
            self._user_post(seed.get("token"), incremental)
            if not self.harvest_result.success:
                break

    def _user_post(self, blog_name, incremental):
        log.info("Harvesting user %s. Incremental is %s.", blog_name, incremental)
        assert blog_name

        # Get offset from state_store
        last_post = self.state_store.get_state(__name__,
                                               "{}.last_post".format(blog_name)) if incremental else None

        max_last_post = self._process_posts(self.tumblrapi.blog_posts(blogname=blog_name, last_post=last_post,
                                                                      incremental=incremental))
        log.debug("Timeline for %s, archived number of posts %s returned %s tumblr posts.", blog_name,
                  max_last_post, self.harvest_result.stats_summary().get("tumblr posts"))

        # Update state store
        if incremental and max_last_post:
            if not last_post:
                last_post = 0
            self.state_store.set_state(__name__, "{}.last_post".format(blog_name), max_last_post + last_post)

    def _process_posts(self, posts):
        max_offset = 0
        for count, post in enumerate(posts):
            if not count % 100:
                log.debug("Processed %s posts", count)
            if self.stop_event.is_set():
                log.debug("Stopping since stop event set.")
                break
            if 'id' in post:
                self.harvest_result.increment_stats("tumblr posts")
                self._process_options(post)
                max_offset += 1
        return max_offset

    def _process_options(self, post):
        """
        source_url for chat photo video audio,'url' for link
        :param post:
        :return:
        """
        if self.extract_web_resources:
            if 'url' in post:
                self.harvest_result.urls.append(post['url'])
            elif 'source_url' in post:
                self.harvest_result.urls.append(post['source_url'])
        if self.extract_media:
            if post['type'] == 'photo':
                for ph in post['photos']:
                    self.harvest_result.urls.append(ph['original_size']['url'])

    def _create_tumblrarc(self):
        self.tumblrapi = Tumblrarc(self.message["credentials"]["consumer_key"],
                                   self.message["credentials"]["consumer_secret"],
                                   self.message["credentials"]["access_token"],
                                   self.message["credentials"]["access_token_secret"])


if __name__ == "__main__":
    TumblrHarvester.main(TumblrHarvester, QUEUE, [USER_POSTS_ROUTING_KEY])
