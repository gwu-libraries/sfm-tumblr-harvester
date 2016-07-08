# sfm-tumblr-harvester
A basic harvester for Tumblr public post data as part of [Social Feed Manager](https://gwu-libraries.github.io/sfm-ui). 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-tumblr-harvester)

Provides harvesters for [Tumblr API](https://www.tumblr.com/docs/en/api/v2) and harvesting is performed by official API client [pytumblr](https://github.com/tumblr/pytumblr).

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



