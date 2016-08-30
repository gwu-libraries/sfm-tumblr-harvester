# sfm-tumblr-harvester
A basic harvester for Tumblr public post data as part of [Social Feed Manager](https://gwu-libraries.github.io/sfm-ui). 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester)

Provides harvesters for [Tumblr API](https://www.tumblr.com/docs/en/api/v2) and harvesting is performed by tumblrarc which
based on [requests-oauthlib](https://github.com/requests/requests-oauthlib).

## Development

For information on development and running tests, see the [development documentation](http://sfm.readthedocs.io/en/latest/development.html).

When running tests, provide Tumblr credentials either as a `test_config.py` file or environment variable (`TUMBLR_API_KEY`).
An example `test_config.py` looks like:

    TUMBLR_API_KEY = "3jlICwerCIWqEdUdAyuenNyercwkVuXOuYFoxTPafWx8DsUMe2"

### User posts harvest type

Type: tumblr_blog_posts

Api methods called:

  * [/posts](https://www.tumblr.com/docs/en/api/v2#posts)

Required parameters:

  * hostname

Optional parameters:

  * incremental: True (default) or False
 

### Authentication

Required parameters:

  * api_key

