from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester, Msg, CODE_TOKEN_NOT_FOUND
from tumblrarc import Tumblrarc
from tumblr_warc_iter import TumblrWarcIter
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

QUEUE = "tumblr_harvester"
USER_POSTS_ROUTING_KEY = "harvest.start.tumblr.tumblr_blog_posts"


class TumblrHarvester(BaseHarvester):
    def __init__(self, working_path, mq_config=None, debug=False):
        BaseHarvester.__init__(self, working_path, mq_config=mq_config, debug=debug)
        self.tumblrapi = None
        self.extract_web_resources = False
        self.extract_media = False
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

        # Get harvest extract options.
        self.extract_web_resources = self.message.get("options", {}).get("web_resources", False)
        self.extract_media = self.message.get("options", {}).get("media", False)

        for seed in self.message.get("seeds", []):
            self._blog_post(seed.get("uid"), self.incremental)
            if not self.result.success:
                break

    def _blog_post(self, blog_name, incremental):
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
                self.result.warnings.append(Msg(CODE_TOKEN_NOT_FOUND, msg))
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

    def _process_options(self, post):
        """
        source_url for chat photo video audio,'url' for link
        :param post:
        :return:
        """
        if self.extract_web_resources:
            # link type url
            if 'url' in post:
                self.result.urls.append(post['url'])
            # the source url, for audio type, some of has this field
            # using audio_url instead when type is audio
            elif 'source_url' in post and post['type'] != 'audio':
                self.result.urls.append(post['source_url'])
            # audio url
            elif 'audio_url' in post:
                self.result.urls.append(post['audio_url'])
            # video youtube
            elif 'permalink_url' in post:
                self.result.urls.append(post['permalink_url'])
            # directly video url
            elif 'video_url' in post:
                self.result.urls.append(post['video_url'])
            # extract url from text type
            elif 'body' in post:
                self.result.urls.extend(self._extract_html_links(post['body'], 'a', 'href'))

        if self.extract_media:
            if 'photos' in post:
                for ph in post['photos']:
                    self.result.urls.append(ph['original_size']['url'])
            # extract img from text type
            elif 'body' in post:
                self.result.urls.extend(self._extract_html_links(post['body'], 'img', 'src'))

    def _create_tumblrarc(self):
        self.tumblrapi = Tumblrarc(self.message["credentials"]["api_key"])

    def process_warc(self, warc_filepath):
        for count, status in enumerate(TumblrWarcIter(warc_filepath)):
            post = status.item
            if not count % 25:
                log.debug("Processing %s posts", count)
            if "id" in post:
                self.result.increment_stats("tumblr posts")
                if self.incremental:
                    # Update state
                    key = u"{}.since_post_id".format(post["blog_name"])
                    self.state_store.set_state(__name__, key,
                                               max(self.state_store.get_state(__name__, key), post.get("id")))
                self._process_options(post)

    @staticmethod
    def _extract_html_links(text, tag_name, link_type):
        link_lists = []
        if not text:
            return link_lists
        param = {link_type: True}
        soup = BeautifulSoup(text, "html.parser")
        for link in soup.find_all(tag_name, **param):
            # get rid of the \" and \" at the beginning and end
            link_lists.append(link[link_type])
        return link_lists


if __name__ == "__main__":
    TumblrHarvester.main(TumblrHarvester, QUEUE, [USER_POSTS_ROUTING_KEY])
