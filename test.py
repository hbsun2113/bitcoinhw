#!/usr/bin/env python
# coding: utf-8

import pyjsonrpc

http_client = pyjsonrpc.HttpClient(
    url = "http://39.108.176.167:8080",
    #url = "http://www.baidu.com/",
    username = "Username123",
    password = "Password123"
)
#print http_client.__dict__
#print (help(http_client))
print http_client.call("add", 1, 2)
# Result: 3
print 1213
# It is also possible to use the *method* name as *attribute* name.
print http_client.add(1, 2)
# Result: 3

# Notifications send messages to the server, without response.
http_client.notify("add", 3, 4)