from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester, Msg, CODE_TOKEN_NOT_FOUND
from tumblrarc import Tumblrarc
from tumblr_warc_iter import TumblrWarcIter
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)

QUEUE = "tumblr_harvester"
USER_POSTS_ROUTING_KEY = "harvest.start.tumblr.tumblr_blog_posts"


class TumblrHarvester(BaseHarvester):
    def __init__(self, working_path, mq_config=None, debug=False, debug_warcprox=False, tries=3):
        BaseHarvester.__init__(self, working_path, mq_config=mq_config, debug=debug, debug_warcprox=debug_warcprox,
                               tries=tries)
        self.tumblrapi = None
        self.incremental = False

    def harvest_seeds(self):
        self._create_tumblrarc()

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "tumblr_blog_posts":
            self.blog_posts()
        else:
            raise KeyError

    def blog_posts(self):
        self.incremental = self.message.get("options", {}).get("incremental", False)

        for seed in self.message.get("seeds", []):
            self._blog_post(seed.get("uid"), seed["id"], self.incremental)
            if not self.result.success:
                break

    def _blog_post(self, blog_name, seed_id, incremental):
        log.info(u"Harvesting blog %s. Incremental is %s.", blog_name, incremental)
        assert blog_name
        try:
            # Get the post id that record in state_store
            since_post_id = self.state_store.get_state(__name__,
                                                       u"{}.since_post_id".format(blog_name)) if incremental else None

            self._harvest_posts(self.tumblrapi.blog_posts(blog_name, since_post_id=since_post_id))
        except HTTPError as e:
            if e.response.status_code == 404:
                msg = "Blog hostname {} probably invalid".format(blog_name)
                log.exception(msg)
                self.result.warnings.append(Msg(CODE_TOKEN_NOT_FOUND, msg, seed_id=seed_id))
            else:
                raise e

    def _harvest_posts(self, posts):
        # max_post_id = None
        for count, post in enumerate(posts):
            if not count % 25:
                log.debug("Harvested %s posts", count)
            if self.stop_harvest_seeds_event.is_set():
                log.debug("Stopping since stop event set.")
                break
            if 'id' in post:
                self.result.harvest_counter['tumblr posts'] += 1

    def _create_tumblrarc(self):
        self.tumblrapi = Tumblrarc(self.message["credentials"]["api_key"])

    def process_warc(self, warc_filepath):
        # Need to keep track of original since_post_ids
        since_post_ids = {}
        for count, status in enumerate(TumblrWarcIter(warc_filepath)):
            post = status.item
            # If not incremental, then use all posts.
            # If incremental and this is the first run (there is no state),
            # then set state to the first post, but use all posts.
            # If incremental and this is not the first run (there is a state),
            # then set the state to the first post, but only use posts that
            # are greater than the original state.
            if not count % 25:
                log.debug("Processing %s posts", count)
            if "id" in post:
                post_id = post.get("id")
                if not self.incremental:
                    self.result.increment_stats("tumblr posts")
                else:
                    key = u"{}.since_post_id".format(post["blog_name"])
                    since_post_id = self.state_store.get_state(__name__, key) or 0
                    if key not in since_post_ids:
                        since_post_ids[key] = since_post_id
                    if post_id > since_post_id:
                        # Update state
                        self.state_store.set_state(__name__, key,  post_id)
                    if post_id > since_post_ids[key]:
                        self.result.increment_stats("tumblr posts")


if __name__ == "__main__":
    TumblrHarvester.main(TumblrHarvester, QUEUE, [USER_POSTS_ROUTING_KEY])
