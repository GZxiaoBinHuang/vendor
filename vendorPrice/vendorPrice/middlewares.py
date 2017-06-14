# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

import random
from settings import PROXIES
from settings import USER_AGENTS 

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        proxy = random.choice(PROXIES)
        #request.meta['proxy'] = proxy
        ua = random.choice(USER_AGENTS)
        request.headers.setdefault('User-Agent', ua)
