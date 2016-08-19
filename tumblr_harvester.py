from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester, Msg, CODE_TOKEN_NOT_FOUND
from tumblrarc import Tumblrarc
from requests.exceptions import HTTPError


log = logging.getLogger(__name__)

QUEUE = "tumblr_harvester"
USER_POSTS_ROUTING_KEY = "harvest.start.tumblr.tumblr_blog_posts"


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
        if harvest_type == "tumblr_blog_posts":
            self.blog_posts()
        else:
            raise KeyError

    def blog_posts(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        # Get harvest extract options.
        self.extract_web_resources = self.message.get("options", {}).get("web_resources", False)
        self.extract_media = self.message.get("options", {}).get("media", False)

        for seed in self.message.get("seeds", []):
            self._blog_post(seed.get("uid"), incremental)
            if not self.harvest_result.success:
                break

    def _blog_post(self, blog_name, incremental):
        log.info(u"Harvesting blog %s. Incremental is %s.", blog_name, incremental)
        assert blog_name
        try:
            # Get the post id that record in state_store
            since_post_id = self.state_store.get_state(__name__,
                                                   u"{}.since_post_id".format(blog_name)) if incremental else None

            max_post_id = self._process_posts(self.tumblrapi.blog_posts(blog_name, since_post_id=since_post_id))
            log.debug(u"Searching blog posts for %s, since posts %s returned %s tumblr posts.", blog_name,
                      since_post_id, self.harvest_result.stats_summary().get("tumblr posts"))

            # Update state store
            if incremental and max_post_id:
                self.state_store.set_state(__name__, u"{}.since_post_id".format(blog_name), max_post_id)
        except HTTPError as e:
            if e.response.status_code == 404:
                msg = "Blog hostname {} probably invalid".format(blog_name)
                log.exception(msg)
                self.harvest_result.warnings.append(Msg(CODE_TOKEN_NOT_FOUND, msg))
            else:
                raise e

    def _process_posts(self, posts):
        max_post_id = None
        for count, post in enumerate(posts):
            if not count % 25:
                log.debug("Processed %s posts", count)
            if self.stop_event.is_set():
                log.debug("Stopping since stop event set.")
                break
            if 'id' in post:
                max_post_id = max(max_post_id, post['id'])
                self.harvest_result.increment_stats("tumblr posts")
                self._process_options(post)
        return max_post_id

    def _process_options(self, post):
        """
        source_url for chat photo video audio,'url' for link
        :param post:
        :return:
        """
        if self.extract_web_resources:
            # link type url
            if 'url' in post:
                self.harvest_result.urls.append(post['url'])
            # the source url, for audio type, some of has this field
            # using audio_url instead when type is audio
            elif 'source_url' in post and post['type'] != 'audio':
                self.harvest_result.urls.append(post['source_url'])
            # audio url
            elif 'audio_url' in post:
                self.harvest_result.urls.append(post['audio_url'])
            # video youtube
            elif 'permalink_url' in post:
                self.harvest_result.urls.append(post['permalink_url'])
            # directly video url
            elif 'video_url' in post:
                self.harvest_result.urls.append(post['video_url'])

        if self.extract_media:
            if 'photos' in post:
                for ph in post['photos']:
                    self.harvest_result.urls.append(ph['original_size']['url'])

    def _create_tumblrarc(self):
        self.tumblrapi = Tumblrarc(self.message["credentials"]["api_key"])


if __name__ == "__main__":
    TumblrHarvester.main(TumblrHarvester, QUEUE, [USER_POSTS_ROUTING_KEY])
