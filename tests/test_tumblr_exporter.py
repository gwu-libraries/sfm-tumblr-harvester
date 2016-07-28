#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import tests
import vcr as base_vcr
from tests.tumblrposts import text_post, link_post, chat_post, photo_post, audio_post, video_post
from tumblr_exporter import TumblrExporter, TumblrStatusTable
from datetime import datetime
import os
import tempfile
import shutil

vcr = base_vcr.VCR(
    cassette_library_dir='tests/fixtures',
    record_mode='once',
)


class TestTumblrStatusTable(tests.TestCase):
    def test_tex_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(text_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(147333929711, row[1])
        self.assertEqual('text', row[3])
        self.assertEqual('Documenting daily life in Colombia through illustration', row[5])
        self.assertEqual("Just over a month ago", row[6])
        self.assertEqual("https://tmblr.co/ZtR4Sx29DoLhl", row[9])

    def test_chat_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(chat_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(12290684312, row[1])
        self.assertEqual('chat', row[3])
        self.assertEqual('Pulaar Proverbs (My Favorites) (via mikadoo)', row[5])
        self.assertEqual("Baasal warataa kono na tampina Poverty does not kill but makes one tired", row[6])
        self.assertEqual("https://tmblr.co/ZtR4SxBSbFMO", row[9])

    def test_link_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(link_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(147299875398, row[1])
        self.assertEqual('link', row[3])
        self.assertEqual('7 reasons Peace Corps Volunteers make the best startup workers', row[5])
        self.assertEqual("Everything I had learned during my two years in Armenia.", row[6])
        self.assertEqual("https://tmblr.co/ZtR4Sx29BmRf6", row[9])

    def test_photo_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(photo_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(147311989737, row[1])
        self.assertEqual('photo', row[3])
        self.assertEqual('the practical lesson I had today with Chris', row[5])
        self.assertEqual("We had our second lesson that involved cooking traditional dishes.", row[6])
        self.assertEqual("https://tmblr.co/ZtR4Sx29CUfFf", row[9])

    def test_audio_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(audio_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(143653757153, row[1])
        self.assertEqual('audio', row[3])
        self.assertEqual('Sound Saturday', row[5])
        self.assertEqual("rcpc:\n\nSound Saturday\nWhat does a classroom in Moldova sound like", row[6])
        self.assertEqual("https://tmblr.co/ZtR4Sx25oRc3X", row[9])

    def test_video_exporter_row(self):
        table = TumblrStatusTable(None, None, None, None, None)
        row = table._row(video_post)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual(147341360917, row[1])
        self.assertEqual('video', row[3])
        self.assertEqual('Colegio kids dancing a traditional Peruvian dance in costume', row[5])
        self.assertEqual("thepetersonsnewgroove:\n\nColegio kids dancing a traditional Peruvian dance in costume",
                         row[6])
        self.assertEqual("https://tmblr.co/ZtR4Sx29EEhyL", row[9])


class TestTumblrExporterVcr(tests.TestCase):
    def setUp(self):
        self.warc_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warcs")
        self.exporter = TumblrExporter("http://127.0.0.1:8080", warc_base_path=self.warc_base_path)
        self.exporter.routing_key = "export.start.tumblr.tumblr_blog_posts"
        self.export_path = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.export_path):
            shutil.rmtree(self.export_path)

    @vcr.use_cassette()
    def test_export_collection(self):
        export_message = {
            "id": "test1",
            "type": "tumblr_blog_posts",
            "collection": {
                "id": "afe49fc673ab4380909e06f43b46a990"
            },
            "format": "csv",
            "path": self.export_path
        }

        self.exporter.message = export_message
        self.exporter.on_message()

        self.assertTrue(self.exporter.export_result.success)
        csv_filepath = os.path.join(self.export_path, "test1.csv")
        self.assertTrue(os.path.exists(csv_filepath))
        with open(csv_filepath, "r") as f:
            lines = f.readlines()
        self.assertEqual(301, len(lines))


class TestTumblrStatusTableVcr(tests.TestCase):
    def setUp(self):
        warc_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warcs")
        self.warc_paths = (os.path.join(warc_base_path,
                                        "tumblr_demo.warc.gz"))

    def test_table(self):
        table = TumblrStatusTable(self.warc_paths, False, None, None, None)
        count = 0
        for count, row in enumerate(table):
            if count == 0:
                # check the fields on the right way
                self.assertEqual("created_at", row[0])
                self.assertEqual("post_text", row[6])
            if count == 2:
                # testing the second row
                self.assertEqual(147244283789, row[1])
                self.assertEqual("Boxed Spirits: Franny Zooey and Everyman by Corcoran School Book "
                                 "Arts professor Kerry McAleer-Keeler takes inspiration from J....", row[5])
                self.assertEqual('https://tmblr.co/ZWQXzj298SNUD', row[9])
        # the demo has collect twice for the first post,so it's 50+1
        self.assertEqual(51, count)
