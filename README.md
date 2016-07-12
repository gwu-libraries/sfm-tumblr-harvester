# sfm-tumblr-harvester
A basic harvester for Tumblr public post data as part of [Social Feed Manager](https://gwu-libraries.github.io/sfm-ui). 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester)

Provides harvesters for [Tumblr API](https://www.tumblr.com/docs/en/api/v2) and harvesting is performed by tumblrarc which based on [requests-oauthlib](https://github.com/requests/requests-oauthlib).

# Install
```bash
git clone https://github.com/gwu-libraries/sfm-tumblr-harvester
cd sfm-tumblr-harvester
pip install -r requirements/requirements.txt
```

# Ready to work
* Sign up an account at [Tumblr](https://www.tumblr.com).
* Register an application at [here](https://www.tumblr.com/oauth/apps) to get your `CONSUMER_KEY`, `CONSUMER_SECRET`. 
* Provide your `CONSUMER_KEY` and `CONSUMER_SECRET` and get your access token at [here]( https://api.tumblr.com/console).
* Once you are succeed authorized your APP, click the `Show Keys` button at the top-right.
* An example of the keys looks like (the following keys are invalid):

    ```bash
    CONSUMER_KEY = "3jlICwerCIWqEdUdAyuenNyercwkVuXOuYFoxTPafWx8DsUMe2"
    CONSUMER_SECRET = "sTCdLJ9kdfgEwTPoYIdfdsteF0XB8WiHlczLx0GgvzRim1L47n"
    ACCESS_TOKEN = "sdrsaPx5FtpJ0tfZAG13kMZMjenouGsdJw9W7ssK6husepcFoWg"
    ACCESS_TOKEN_SECRET = "0VxKNAMSiNO8IT6PsdattmUsdsfI5X1hP4usBNZLllgkhwsdQiY"
    ________________________________________________________________________
    API_KEY = "3jlICwerCIWqEdUdAyuenNyercwkVuXOuYFoxTPafWx8DsUMe2"
    ```

> The corresponding keys for testing needs add the prefix `TUMBLR_`.

## Tests

### Unit tests
    python -m unittest discover

### Integration tests (inside docker containers)
1. Install [Docker](https://docs.docker.com/installation/) and [Docker-Compose](https://docs.docker.com/compose/install/).
2. Provide the keys and secrets to the tests. This can be done in the way [sfm-twitter-harvest](https://github.com/gwu-libraries/sfm-twitter-harvester#integration-tests-inside-docker-containers) do.  An example looks like:

    ```bash
    TUMBLR_CONSUMER_KEY = "3jlICwerCIWqEdUdAyuenNyercwkVuXOuYFoxTPafWx8DsUMe2"
    TUMBLR_CONSUMER_SECRET = "sTCdLJ9kdfgEwTPoYIdfdsteF0XB8WiHlczLx0GgvzRim1L47n"
    TUMBLR_ACCESS_TOKEN = "sdrsaPx5FtpJ0tfZAG13kMZMjenouGsdJw9W7ssK6husepcFoWg"
    TUMBLR_ACCESS_TOKEN_SECRET = "0VxKNAMSiNO8IT6PsdattmUsdsfI5X1hP4usBNZLllgkhwsdQiY"
    ```

3. Start up the containers.

        docker-compose -f docker/dev.docker-compose.yml up -d

4. Run the tests.

        docker exec docker_sfmtwitterstreamharvester_1 python -m unittest discover

5. Shutdown containers.

        docker-compose -f docker/dev.docker-compose.yml kill
        docker-compose -f docker/dev.docker-compose.yml rm -v --force
        
  
### User posts harvest type

Type: tumblr_user_posts

Api methods called:

  * [/posts](https://www.tumblr.com/docs/en/api/v2#posts)

Required parameters:

  * hostname

Optional parameters:

  * incremental: True (default) or False
 

### Authentication

Required parameters:

  * consumer_key
  * consumer_secret
  * access_token
  * access_token_secret

