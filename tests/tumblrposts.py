#!/usr/bin/env python
# -*- coding: utf-8 -*-

text_post={
        "blog_name": "peacecorps",
        "id": 147333929711,
        "post_url": "http://peacecorps.tumblr.com/post/147333929711/documenting-daily-life-in-colombia-through",
        "slug": "documenting-daily-life-in-colombia-through",
        "type": "text",
        "date": "2016-07-13 08:48:11 GMT",
        "timestamp": 1468399691,
        "state": "published",
        "format": "html",
        "reblog_key": "r3WZi76g",
        "tags": [
          "art",
          "illustration",
          "drawing",
          "peace corps",
          "colombia",
          "peace corps colombia",
          "peace corps volunteer",
          "peace corps life"
        ],
        "short_url": "https://tmblr.co/ZtR4Sx29DoLhl",
        "summary": "Documenting daily life in Colombia through illustration",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 11,
        "title": "Documenting daily life in Colombia through illustration",
         "body": "<p>A research assistant to a professor in the <a href=\"https://elliott.gwu.edu/\">Elliott School of International Affairs</a> came to one of GW Libraries&rsquo; <a href=\"https://library.gwu.edu/services/computers-wireless/coding\">programming and software development consultations</a> to ask for help downloading United Nations (UN) Security Council resolutions. The resolutions were <a href=\"http://www.un.org/en/sc/documents/resolutions/\">available on the UN website</a> as PDFs.</p><figure data-orig-width=\"666\" data-orig-height=\"514\" class=\"tmblr-full\"><img src=\"https://65.media.tumblr.com/e29ca96f6a4d109d3ae8a03fcea0a3d2/tumblr_inline_o3ojawjiNw1t0f420_540.png\" data-orig-width=\"666\" data-orig-height=\"514\"/></figure><p>I&rsquo;ll skip the part where I tried using wget and tried wrestling with the UN&rsquo;s inscrutable <a href=\"http://www.un.org/en/official-documents-system-search/index.html\">document search system</a> and get my rant out of the way: <i>The UN (or any similar organization) should make it easy to download their publicly available documents.</i></p><p>I reached for python using the <a href=\"https://github.com/kennethreitz/requests\">requests</a> and <a href=\"http://www.crummy.com/software/BeautifulSoup/\">BeautifulSoup</a> libraries. </p><figure data-orig-width=\"652\" data-orig-height=\"395\" class=\"tmblr-full\"><img src=\"https://67.media.tumblr.com/86c495667eb9cd2fa436361ab6448aa0/tumblr_inline_o3ojbiXb2K1t0f420_540.png\" data-orig-width=\"652\" data-orig-height=\"395\"/></figure><p><br/></p><pre><code>s = requests.Session()\nr = s.get(\"{}/en/sc/documents/resolutions/{}.shtml\".format(base_url, year))\nr.raise_for_status()\npage = BeautifulSoup(r.text)\nfor link in page.findAll(\"a\"):\n    # Some of the pages have relative links; some have absolute.\n    if link[\"href\"].startswith(\"/en/ga/search/view_doc.asp?symbol=S/RES\"):\n        fetch_doc(\"{}{}\".format(base_url, link[\"href\"]), s)\n    elif link[\"href\"].startswith(\"http://www.un.org/en/ga/search/view_doc.asp?symbol=S/RES\"):\n        fetch_doc(link[\"href\"], s)\n</code></pre><p>Each of these links is to a frame, so that a header can be included to provide links to the document in other languages (since this is the UN after all). The HTML for the main frame is:</p><pre><code>&lt;frame src=\"http://daccess-ods.un.org/access.nsf/Get?Open&amp;amp;DS=S/RES/1966(2010)&amp;amp;Lang=E\" name=\"mainFrame\" title=\"PDF Document\"&gt;\n</code></pre><p>One would expect/hope that this would be a link to the PDF, but it isn&rsquo;t. </p><pre><code>&lt;html&gt;\n&lt;head&gt;\n&lt;/head&gt;\n&lt;body text=\"#000000\"&gt;\n&lt;META HTTP-EQUIV=\"refresh\" CONTENT=\"0; URL=/TMP/3044276.83353424.html\"&gt;\n&lt;/body&gt;\n&lt;/html&gt;\n</code></pre><p>I had to look up <a href=\"https://en.wikipedia.org/wiki/Meta_refresh\">HTTP-EQUIV=refresh</a>, but to the best I can tell it is a bad way to do a redirect. Unfortunately, it&rsquo;s a form of redirect that is not handled by requests, so I had to do it myself:</p><pre><code>page = BeautifulSoup(r.text)\nlink = page.find(\"meta\", attrs={\"http-equiv\": \"refresh\"})\nurl = \"http://daccess-ods.un.org{}\".format(link[\"content\"][7:])\nr = s.get(url)\n</code></pre><p>And here&rsquo;s where I&rsquo;m sure I had gone down a rabbit hole, as the page returned is another frame with another HTTP-EQUIV=refresh:</p><pre><code>&lt;html&gt;\n&lt;head&gt;\n&lt;meta http-equiv=\"Content-Type\" content=\"text/html; charset=windows-1252\"&gt;\n&lt;META HTTP-EQUIV=\"refresh\" CONTENT=\"1; URL=https://documents-dds-ny.un.org/doc/UNDOC/GEN/N00/812/31/PDF/N0081231.pdf?OpenElement\"&gt;\n&lt;base target=\"_top\"&gt;\n&lt;/head&gt;\n&lt;frameset ROWS=\"0,100%\" framespacing=\"0\" FrameBorder=\"0\" Border=\"0\"&gt;\n  &lt;frame name=\"footer\" scrolling=\"no\" noresize target=\"main\" src=\"https://documents-dds-ny.un.org/prod/ods_mother.nsf?Login&amp;Username=freeods2&amp;Password=1234\" marginwidth=\"0\" marginheight=\"0\"&gt;\n  &lt;frame name=\"main\" src=\"\" scrolling=\"auto\" target=\"_top\"&gt;\n&lt;/frameset&gt;\n&lt;/html&gt;\n</code></pre><p>So fetch <code><a href=\"https://documents-dds-ny.un.org/doc/UNDOC/GEN/N00/812/31/PDF/N0081231.pdf\">https://documents-dds-ny.un.org/doc/UNDOC/GEN/N00/812/31/PDF/N0081231.pdf</a></code> and get the PDF, right?  Wrong &ndash; you get an HTML page that says this:</p><figure class=\"tmblr-full\" data-orig-height=\"102\" data-orig-width=\"606\"><img src=\"https://66.media.tumblr.com/c9a37a68e3a16e0155652552035c10a9/tumblr_inline_o3ojciXLcL1t0f420_540.png\" data-orig-height=\"102\" data-orig-width=\"606\"/></figure><p>(Since this is the UN, I also received the message in French too.)</p><p>The browser successfully fetches and renders the PDF, so I knew it was possible.  I tried setting various headers (accept, accept-encoding, accept-language, user-agent) and passing back the cookies. Nothing worked. I noticed that the cookies in the script and the cookies in the browser were different, but didn&rsquo;t know what to make of this.  Here is where I admitted defeat, emailed the research assistant that it wasn&rsquo;t possible, and went to have lunch with my wife.</p><p>I don&rsquo;t know if was something in the Indian food or just the mental space from the problem, but that last frameset was niggling at the back of my mind.  What was the purpose of the frameset and especially the footer that called <a href=\"https://documents-dds-ny.un.org/prod/ods_mother.nsf?Login&amp;Username=freeods2&amp;Password=1234?\">https://documents-dds-ny.un.org/prod/ods_mother.nsf?Login&amp;Username=freeods2&amp;Password=1234?</a> (Also, why would a username and password be available in cleartext, but I won&rsquo;t touch that one.) And why were the cookies different? And then it hit me &ndash; maybe the purpose of that footer was to set cookies. So I added a call to it, but did nothing with the result:</p><pre><code>s.get(\"https://documents-dds-ny.un.org/prod/ods_mother.nsf?Login&amp;Username=freeods2&amp;Password=1234\")\n</code></pre><p>This time, fetching the PDF and writing it to a file worked:</p><pre><code>r = s.get(url, headers={\"accept\": \"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\", \"accept-encoding\": \"gzip, deflate, sdch\", \"accept-language\": \"en-US,en;q=0.8\", \"user-agent\": \"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.109 Safari/537.36\", \"referer\": r.url}, stream=True)\n    r.raise_for_status()\n    print filename\n    with open(filename, 'wb') as fd:\n        for chunk in r.iter_content(2048):\n            fd.write(chunk)\n</code></pre></p>",
        "reblog": {
          "tree_html": "",
          "comment": "<p>Just over a month ago, I finished my Peace Corps service in a peri-urban fishing community located 25 minutes north of Cartagena, Colombia.\n\nI\'m still thinking about scenes that I need to draw—the lime green cart filled with fritos surrounded by red plastic tables and chairs, the aggressive hat vendors in the Centro and the bustling, chaotic Bazurto Mercado. Cartagena continues to inspire me.\n\nThroughout the last 27 months in Colombia, I documented my experience through a series of full-color illustrations and daily drawings. During training, before I knew much about Colombia, I began making collages of scenery from the beaches outside of Barranquilla, typical meals, and street scenes with kids riding bikes and playing soccer. However, on a trip back to the States, I discovered a set of Prismacolor markers that I hadn\'t used since high school. The fuchsias, turquoises, and bright yellows reminded me of the colors I saw everyday in Cartagena, and I hadn\'t realized the extent of their absence until I was once again surrounded by the calm blues, whites, and muted tones of a New England summer.\n\nRead the full story</p>"
        },
        "trail": [
          {
            "blog": {
              "name": "peacecorps",
              "active": True,
              "theme": {
                "header_full_width": 828,
                "header_full_height": 315,
                "header_focus_width": 551,
                "header_focus_height": 310,
                "avatar_shape": "circle",
                "background_color": "#F6F6F6",
                "body_font": "Helvetica Neue",
                "header_bounds": "2,689,312,138",
                "header_image": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4.jpg",
                "header_image_focused": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/rCgo83et9/tumblr_static_tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_focused_v3.jpg",
                "header_image_scaled": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_2048_v2.jpg",
                "header_stretch": True,
                "link_color": "#529ECC",
                "show_avatar": True,
                "show_description": True,
                "show_header_image": True,
                "show_title": True,
                "title_color": "#444444",
                "title_font": "Helvetica Neue",
                "title_font_weight": "bold"
              },
              "share_likes": True,
              "share_following": False
            },
            "post": {
              "id": "147333929711"
            },
            "content_raw": "<p>Just over a month ago, I finished my Peace Corps service in a peri-urban fishing community located 25 minutes north of Cartagena, Colombia.\n\nI\'m still thinking about scenes that I need to draw—the lime green cart filled with fritos surrounded by red plastic tables and chairs, the aggressive hat vendors in the Centro and the bustling, chaotic Bazurto Mercado. Cartagena continues to inspire me.\n\nThroughout the last 27 months in Colombia, I documented my experience through a series of full-color illustrations and daily drawings. During training, before I knew much about Colombia, I began making collages of scenery from the beaches outside of Barranquilla, typical meals, and street scenes with kids riding bikes and playing soccer. However, on a trip back to the States, I discovered a set of Prismacolor markers that I hadn\'t used since high school. The fuchsias, turquoises, and bright yellows reminded me of the colors I saw everyday in Cartagena, and I hadn\'t realized the extent of their absence until I was once again surrounded by the calm blues, whites, and muted tones of a New England summer.\n\nRead the full story</p>",
            "content": "<p>Just over a month ago, I finished my Peace Corps service in a peri-urban fishing community located 25 minutes north of Cartagena, Colombia.\n\nI\'m still thinking about scenes that I need to draw—the lime green cart filled with fritos surrounded by red plastic tables and chairs, the aggressive hat vendors in the Centro and the bustling, chaotic Bazurto Mercado. Cartagena continues to inspire me.\n\nThroughout the last 27 months in Colombia, I documented my experience through a series of full-color illustrations and daily drawings. During training, before I knew much about Colombia, I began making collages of scenery from the beaches outside of Barranquilla, typical meals, and street scenes with kids riding bikes and playing soccer. However, on a trip back to the States, I discovered a set of Prismacolor markers that I hadn\'t used since high school. The fuchsias, turquoises, and bright yellows reminded me of the colors I saw everyday in Cartagena, and I hadn\'t realized the extent of their absence until I was once again surrounded by the calm blues, whites, and muted tones of a New England summer.\n\nRead the full story</p>",
            "is_current_item": True,
            "is_root_item": True
          }
        ],
        "can_send_in_message": True
}

chat_post = {
        "blog_name": "peacecorps",
        "id": 12290684312,
        "post_url": "http://peacecorps.tumblr.com/post/12290684312/pulaar-proverbs-my-favorites-via-mikadoo",
        "slug": "pulaar-proverbs-my-favorites-via-mikadoo",
        "type": "chat",
        "date": "2011-11-03 18:48:00 GMT",
        "timestamp": 1320346080,
        "state": "published",
        "format": "html",
        "reblog_key": "Ml4c3tiI",
        "tags": [
          "reblog",
          "Senegal",
          "Africa",
          "Peace Corps",
          "Peace Corps Volunteer",
          "language"
        ],
        "short_url": "https://tmblr.co/ZtR4SxBSbFMO",
        "summary": "Pulaar Proverbs (My Favorites) (via mikadoo)",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 21,
        "source_url": "http://maddyandpaulinsenegal.wordpress.com/pulaar-proverbs/",
        "source_title": "maddyandpaulinsenegal.wordpress.com",
        "title": "Pulaar Proverbs (My Favorites) (via mikadoo)",
        "body": "Baasal warataa kono na tampina Poverty does not kill but makes one tired",
        "dialogue": [
          {
            "name": "",
            "label": "",
            "phrase": "Baasal warataa kono na tampina"
          },
          {
            "name": "",
            "label": "",
            "phrase": "Poverty does not kill but makes one tired"
          },
          {
            "name": "",
            "label": "",
            "phrase": "***"
          },
          {
            "name": "",
            "label": "",
            "phrase": "Si bahe cumɗi gooto fof ñifata ko waare mum"
          },
          {
            "name": "",
            "label": "",
            "phrase": "If the beards are all on fire, each person must put out his own beard"
          },
          {
            "name": "",
            "label": "",
            "phrase": "***"
          },
          {
            "name": "",
            "label": "",
            "phrase": "ɓe nengasa ɓe ne nguuba yaajay kono luggidtaa"
          },
          {
            "name": "",
            "label": "",
            "phrase": "If some are digging and some are burying it will be wide but never deep"
          },
          {
            "name": "",
            "label": "",
            "phrase": "***"
          },
          {
            "name": "",
            "label": "",
            "phrase": "Mawɗo ina jooɗoo yi'ii cukalel ɗaroo roŋku yi'ude"
          },
          {
            "name": "",
            "label": "",
            "phrase": "A seated elder sees what a standing child misses"
          }
        ],
        "can_send_in_message": True
}

link_post={
        "blog_name": "peacecorps",
        "id": 147299875398,
        "post_url": "http://peacecorps.tumblr.com/post/147299875398/7-reasons-peace-corps-volunteers-make-the-best",
        "slug": "7-reasons-peace-corps-volunteers-make-the-best",
        "type": "link",
        "date": "2016-07-12 18:24:22 GMT",
        "timestamp": 1468347862,
        "state": "published",
        "format": "html",
        "reblog_key": "Tzhsl1gD",
        "tags": [
          "peace corps",
          "peace corps volunteer",
          "returned peace corps volunteer",
          "peace corps life",
          "startup"
        ],
        "short_url": "https://tmblr.co/ZtR4Sx29BmRf6",
        "summary": "7 reasons Peace Corps Volunteers make the best startup workers",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 8,
        "title": "7 reasons Peace Corps Volunteers make the best startup workers",
        "url": "https://www.peacecorps.gov/stories/7-reasons-peace-corps-volunteers-make-the-best-startup-workers/",
        "link_author": None,
        "excerpt": "Everything I had learned during my two years in Armenia.",
        "publisher": "peacecorps.gov",
        "description": "\"3. We make magic happen with limited resources.\"",
        "reblog": {
          "tree_html": "",
          "comment": "<p>\"3. We make magic happen with limited resources.\"</p>"
        },
        "trail": [
          {
            "blog": {
              "name": "peacecorps",
              "active": True,
              "theme": {
                "header_full_width": 828,
                "header_full_height": 315,
                "header_focus_width": 551,
                "header_focus_height": 310,
                "avatar_shape": "circle",
                "background_color": "#F6F6F6",
                "body_font": "Helvetica Neue",
                "header_bounds": "2,689,312,138",
                "header_image": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4.jpg",
                "header_image_focused": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/rCgo83et9/tumblr_static_tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_focused_v3.jpg",
                "header_image_scaled": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_2048_v2.jpg",
                "header_stretch": True,
                "link_color": "#529ECC",
                "show_avatar": True,
                "show_description": True,
                "show_header_image": True,
                "show_title": True,
                "title_color": "#444444",
                "title_font": "Helvetica Neue",
                "title_font_weight": "bold"
              },
              "share_likes": True,
              "share_following": False
            },
            "post": {
              "id": "147299875398"
            },
            "content_raw": "<p>\"3. We make magic happen with limited resources.\"</p>",
            "content": "<p>\"3. We make magic happen with limited resources.\"</p>",
            "is_current_item": True,
            "is_root_item": True
          }
        ],
        "can_send_in_message": True
}

photo_post= {
        "blog_name": "peacecorps",
        "id": 147311989737,
        "post_url": "http://peacecorps.tumblr.com/post/147311989737/lehmanrl-theres-a-before-photo-set-for-the",
        "slug": "lehmanrl-theres-a-before-photo-set-for-the",
        "type": "photo",
        "date": "2016-07-12 23:12:09 GMT",
        "timestamp": 1468365129,
        "state": "published",
        "format": "html",
        "reblog_key": "gyshJGiu",
        "tags": [
          "peace corps",
          "peace corps life",
          "moldova",
          "peace corps moldova",
          "peace corps volunteer",
          "cooking"
        ],
        "short_url": "https://tmblr.co/ZtR4Sx29CUfFf",
        "summary": "the practical lesson I had today with Chris",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 12,
        "source_url": "http://lehmanrl.tumblr.com/post/146996540968/theres-a-before-photo-set-for-the-practical",
        "source_title": "lehmanrl",
        "caption": "We had our second lesson that involved cooking traditional dishes.",
        "reblog": {
          "tree_html": "",
          "comment": "<p>lehmanrl:\n\nThere\'s a \"before\" photo set for the practical lesson I had today with Chris\' &amp; my Romanian teacher Mrs. Liuba. We had our second lesson that involved cooking traditional dishes. Today was a delicious day! We made both a savory dish and a sweet dessert.\n\nPăstăi: We made this first. It reminds me of a dish Chris used to make that we called \"Cottage Ham Not\" (because it was cottage ham but not at all, because it did NOT have ham in it). We prepped and cooked potatoes, green beans, and onions, flavored with fresh garlic, salt, and bay leaves.\n\nClătite: We made dessert clătite, sweet crepes with a sweet cow cheese stuffing to which we added dried blueberries. We also made a little sweet cream to put on top and grated on milk chocolate.\n\nI hope to continue these practical cooking lessons with Liuba as they are both a lot of fun as well as teach me cool skills. Liuba is a talented cook as well as teacher.</p>"
        },
        "trail": [
          {
            "blog": {
              "name": "peacecorps",
              "active": True,
              "theme": {
                "header_full_width": 828,
                "header_full_height": 315,
                "header_focus_width": 551,
                "header_focus_height": 310,
                "avatar_shape": "circle",
                "background_color": "#F6F6F6",
                "body_font": "Helvetica Neue",
                "header_bounds": "2,689,312,138",
                "header_image": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4.jpg",
                "header_image_focused": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/rCgo83et9/tumblr_static_tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_focused_v3.jpg",
                "header_image_scaled": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_2048_v2.jpg",
                "header_stretch": True,
                "link_color": "#529ECC",
                "show_avatar": True,
                "show_description": True,
                "show_header_image": True,
                "show_title": True,
                "title_color": "#444444",
                "title_font": "Helvetica Neue",
                "title_font_weight": "bold"
              },
              "share_likes": True,
              "share_following": False
            },
            "post": {
              "id": "147311989737"
            },
            "content_raw": "<p>lehmanrl:\n\nThere\'s a \"before\" photo set for the practical lesson I had today with Chris\' &amp; my Romanian teacher Mrs. Liuba. We had our second lesson that involved cooking traditional dishes. Today was a delicious day! We made both a savory dish and a sweet dessert.\n\nPăstăi: We made this first. It reminds me of a dish Chris used to make that we called \"Cottage Ham Not\" (because it was cottage ham but not at all, because it did NOT have ham in it). We prepped and cooked potatoes, green beans, and onions, flavored with fresh garlic, salt, and bay leaves.\n\nClătite: We made dessert clătite, sweet crepes with a sweet cow cheese stuffing to which we added dried blueberries. We also made a little sweet cream to put on top and grated on milk chocolate.\n\nI hope to continue these practical cooking lessons with Liuba as they are both a lot of fun as well as teach me cool skills. Liuba is a talented cook as well as teacher.</p>",
            "content": "<p>lehmanrl:\n\nThere\'s a \"before\" photo set for the practical lesson I had today with Chris\' &amp; my Romanian teacher Mrs. Liuba. We had our second lesson that involved cooking traditional dishes. Today was a delicious day! We made both a savory dish and a sweet dessert.\n\nPăstăi: We made this first. It reminds me of a dish Chris used to make that we called \"Cottage Ham Not\" (because it was cottage ham but not at all, because it did NOT have ham in it). We prepped and cooked potatoes, green beans, and onions, flavored with fresh garlic, salt, and bay leaves.\n\nClătite: We made dessert clătite, sweet crepes with a sweet cow cheese stuffing to which we added dried blueberries. We also made a little sweet cream to put on top and grated on milk chocolate.\n\nI hope to continue these practical cooking lessons with Liuba as they are both a lot of fun as well as teach me cool skills. Liuba is a talented cook as well as teacher.</p>",
            "is_current_item": True
          }
        ],
        "image_permalink": "http://peacecorps.tumblr.com/image/147311989737",
        "photos": [
          {
            "caption": "",
            "alt_sizes": [
              {
                "url": "https://67.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_1280.jpg",
                "width": 1080,
                "height": 1080
              },
              {
                "url": "https://66.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_500.jpg",
                "width": 500,
                "height": 500
              },
              {
                "url": "https://66.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_400.jpg",
                "width": 400,
                "height": 400
              },
              {
                "url": "https://67.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_250.jpg",
                "width": 250,
                "height": 250
              },
              {
                "url": "https://66.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_100.jpg",
                "width": 100,
                "height": 100
              },
              {
                "url": "https://66.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_75sq.jpg",
                "width": 75,
                "height": 75
              }
            ],
            "original_size": {
              "url": "https://67.media.tumblr.com/7834065aa3773cd136b35ab440ccc35e/tumblr_o9wem7wIYv1u9rguio1_1280.jpg",
              "width": 1080,
              "height": 1080
            }
          }
        ],
        "can_send_in_message": True
}

audio_post={
        "blog_name": "peacecorps",
        "id": 143653757153,
        "post_url": "http://peacecorps.tumblr.com/post/143653757153/rcpc-sound-saturday-what-does-a-classroom-in",
        "slug": "rcpc-sound-saturday-what-does-a-classroom-in",
        "type": "audio",
        "date": "2016-04-30 23:12:34 GMT",
        "timestamp": 1462057954,
        "state": "published",
        "format": "html",
        "reblog_key": "95wnq07l",
        "tags": [
          "teaching",
          "peace corps",
          "moldova",
          "peace corps moldova",
          "peace corps volunteer"
        ],
        "short_url": "https://tmblr.co/ZtR4Sx25oRc3X",
        "summary": "Sound Saturday",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 4,
        "source_url": "https://soundcloud.com/chris-flowers-8/bingo-at-jennys-school-final",
        "source_title": "SoundCloud / J Chris Flowers",
        "track_name": "Bingo At Jenny's School - Final",
        "caption": "rcpc:\n\nSound Saturday\nWhat does a classroom in Moldova sound like",
        "reblog": {
          "tree_html": "",
          "comment": "<p>rcpc:\n\nSound Saturday\nWhat does a classroom in Moldova sound like? \n\nYou may have read earlier about Rebecca\'s adventures in Fîrlădeni. While there Rebecca observed fellow volunteer Jenny Sayles\'s health education class. Jenny was conducting a review session. To make things fun, they played a game of BINGO!\n\nRebecca recorded 2 minutes of the game. Listen carefully and you\'ll hear students shouting Bingo and may hear other words about health topics that sound familiar. \n\nClose your eyes and press play. It\'s time to go to school.</p>"
        },
        "trail": [
          {
            "blog": {
              "name": "peacecorps",
              "active": True,
              "theme": {
                "header_full_width": 828,
                "header_full_height": 315,
                "header_focus_width": 551,
                "header_focus_height": 310,
                "avatar_shape": "circle",
                "background_color": "#F6F6F6",
                "body_font": "Helvetica Neue",
                "header_bounds": "2,689,312,138",
                "header_image": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4.jpg",
                "header_image_focused": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/rCgo83et9/tumblr_static_tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_focused_v3.jpg",
                "header_image_scaled": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_2048_v2.jpg",
                "header_stretch": True,
                "link_color": "#529ECC",
                "show_avatar": True,
                "show_description": True,
                "show_header_image": True,
                "show_title": True,
                "title_color": "#444444",
                "title_font": "Helvetica Neue",
                "title_font_weight": "bold"
              },
              "share_likes": True,
              "share_following": False
            },
            "post": {
              "id": "143653757153"
            },
            "content_raw": "<p>rcpc:\n\nSound Saturday\nWhat does a classroom in Moldova sound like? \n\nYou may have read earlier about Rebecca\'s adventures in Fîrlădeni. While there Rebecca observed fellow volunteer Jenny Sayles\'s health education class. Jenny was conducting a review session. To make things fun, they played a game of BINGO!\n\nRebecca recorded 2 minutes of the game. Listen carefully and you\'ll hear students shouting Bingo and may hear other words about health topics that sound familiar. \n\nClose your eyes and press play. It\'s time to go to school.</p>",
            "content": "<p>rcpc:\n\nSound Saturday\nWhat does a classroom in Moldova sound like? \n\nYou may have read earlier about Rebecca\'s adventures in Fîrlădeni. While there Rebecca observed fellow volunteer Jenny Sayles\'s health education class. Jenny was conducting a review session. To make things fun, they played a game of BINGO!\n\nRebecca recorded 2 minutes of the game. Listen carefully and you\'ll hear students shouting Bingo and may hear other words about health topics that sound familiar. \n\nClose your eyes and press play. It\'s time to go to school.</p>",
            "is_current_item": True
          }
        ],
        "player": "<iframe src=\"https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F260499686&amp;visual=True&amp;liking=False&amp;sharing=False&amp;auto_play=False&amp;show_comments=False&amp;continuous_play=False&amp;origin=tumblr\" frameborder=\"0\" allowtransparency=\"True\" class=\"soundcloud_audio_player\" width=\"500\" height=\"500\"></iframe>",
        "embed": "<iframe src=\"https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F260499686&amp;visual=True&amp;liking=False&amp;sharing=False&amp;auto_play=False&amp;show_comments=False&amp;continuous_play=False&amp;origin=tumblr\" frameborder=\"0\" allowtransparency=\"True\" class=\"soundcloud_audio_player\" width=\"540\" height=\"540\"></iframe>",
        "plays": 8,
        "audio_url": "https://api.soundcloud.com/tracks/260499686/stream?client_id=3cQaPshpEeLqMsNFAUw1Q",
        "audio_source_url": "https://soundcloud.com/chris-flowers-8/bingo-at-jennys-school-final",
        "is_external": True,
        "audio_type": "soundcloud",
        "can_send_in_message": True
}

video_post={
        "blog_name": "peacecorps",
        "id": 147341360917,
        "post_url": "http://peacecorps.tumblr.com/post/147341360917/thepetersonsnewgroove-colegio-kids-dancing",
        "slug": "thepetersonsnewgroove-colegio-kids-dancing",
        "type": "video",
        "date": "2016-07-13 13:36:11 GMT",
        "timestamp": 1468416971,
        "state": "published",
        "format": "html",
        "reblog_key": "l4XRUPvH",
        "tags": [
          "video",
          "peace corps",
          "peru",
          "peace corps peru",
          "peace corps life",
          "peace corps volunteer"
        ],
        "short_url": "https://tmblr.co/ZtR4Sx29EEhyL",
        "summary": "Colegio kids dancing a traditional Peruvian dance in costume",
        "recommended_source": None,
        "recommended_color": None,
        "highlighted": [],
        "note_count": 8,
        "caption": "thepetersonsnewgroove:\n\nColegio kids dancing a traditional Peruvian dance in costume",
        "reblog": {
          "tree_html": "",
          "comment": "<p>thepetersonsnewgroove:\n\nColegio kids dancing a traditional Peruvian dance in costume</p>"
        },
        "trail": [
          {
            "blog": {
              "name": "peacecorps",
              "active": True,
              "theme": {
                "header_full_width": 828,
                "header_full_height": 315,
                "header_focus_width": 551,
                "header_focus_height": 310,
                "avatar_shape": "circle",
                "background_color": "#F6F6F6",
                "body_font": "Helvetica Neue",
                "header_bounds": "2,689,312,138",
                "header_image": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4.jpg",
                "header_image_focused": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/rCgo83et9/tumblr_static_tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_focused_v3.jpg",
                "header_image_scaled": "https://secure.static.tumblr.com/0375850ca10490e78816545c3e60ed0a/viosyoi/ycpo83et8/tumblr_static_1vgzzqbcsa74o0skwg4o0kcg4_2048_v2.jpg",
                "header_stretch": True,
                "link_color": "#529ECC",
                "show_avatar": True,
                "show_description": True,
                "show_header_image": True,
                "show_title": True,
                "title_color": "#444444",
                "title_font": "Helvetica Neue",
                "title_font_weight": "bold"
              },
              "share_likes": True,
              "share_following": False
            },
            "post": {
              "id": "147341360917"
            },
            "content_raw": "<p>thepetersonsnewgroove:\n\nColegio kids dancing a traditional Peruvian dance in costume</p>",
            "content": "<p>thepetersonsnewgroove:\n\nColegio kids dancing a traditional Peruvian dance in costume</p>",
            "is_current_item": True
          }
        ],
        "video_url": "https://vt.tumblr.com/tumblr_oa44q4JDN91uyyiyx_720.mp4",
        "html5_capable": True,
        "thumbnail_url": "https://31.media.tumblr.com/tumblr_oa44q4JDN91uyyiyx_frame1.jpg",
        "thumbnail_width": 1920,
        "thumbnail_height": 1080,
        "duration": 9,
        "player": [
          {
            "width": 250,
            "embed_code": "\n<video  id='embed-57864aa24c090888786350' class='crt-video crt-skin-default' width='250' height='141' poster='https://66.media.tumblr.com/tumblr_oa44q4JDN91uyyiyx_smart1.jpg' preload='none' data-crt-video data-crt-options='{\"autoheight\":None,\"duration\":9,\"hdUrl\":\"https:\\/\\/api.tumblr.com\\/video_file\\/147341360917\\/tumblr_oa44q4JDN91uyyiyx\\/720\",\"filmstrip\":{\"url\":\"https:\\/\\/66.media.tumblr.com\\/previews\\/tumblr_oa44q4JDN91uyyiyx_filmstrip.jpg\",\"width\":\"200\",\"height\":\"112\"}}' >\n    <source src=\"https://api.tumblr.com/video_file/147341360917/tumblr_oa44q4JDN91uyyiyx/480\" type=\"video/mp4\">\n</video>\n"
          },
          {
            "width": 400,
            "embed_code": "\n<video  id='embed-57864aa24c090888786350' class='crt-video crt-skin-default' width='400' height='225' poster='https://66.media.tumblr.com/tumblr_oa44q4JDN91uyyiyx_smart1.jpg' preload='none' data-crt-video data-crt-options='{\"autoheight\":None,\"duration\":9,\"hdUrl\":\"https:\\/\\/api.tumblr.com\\/video_file\\/147341360917\\/tumblr_oa44q4JDN91uyyiyx\\/720\",\"filmstrip\":{\"url\":\"https:\\/\\/66.media.tumblr.com\\/previews\\/tumblr_oa44q4JDN91uyyiyx_filmstrip.jpg\",\"width\":\"200\",\"height\":\"112\"}}' >\n    <source src=\"https://api.tumblr.com/video_file/147341360917/tumblr_oa44q4JDN91uyyiyx/480\" type=\"video/mp4\">\n</video>\n"
          },
          {
            "width": 500,
            "embed_code": "\n<video  id='embed-57864aa24c090888786350' class='crt-video crt-skin-default' width='500' height='281' poster='https://66.media.tumblr.com/tumblr_oa44q4JDN91uyyiyx_smart1.jpg' preload='none' data-crt-video data-crt-options='{\"autoheight\":None,\"duration\":9,\"hdUrl\":\"https:\\/\\/api.tumblr.com\\/video_file\\/147341360917\\/tumblr_oa44q4JDN91uyyiyx\\/720\",\"filmstrip\":{\"url\":\"https:\\/\\/66.media.tumblr.com\\/previews\\/tumblr_oa44q4JDN91uyyiyx_filmstrip.jpg\",\"width\":\"200\",\"height\":\"112\"}}' >\n    <source src=\"https://api.tumblr.com/video_file/147341360917/tumblr_oa44q4JDN91uyyiyx/480\" type=\"video/mp4\">\n</video>\n"
          }
        ],
        "video_type": "tumblr",
        "can_send_in_message": True
}
