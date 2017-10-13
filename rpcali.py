#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  9 14:41:23 2017

@author: mac
"""
import pyjsonrpc
http_client = pyjsonrpc.HttpClient(url = "http://39.108.176.167:8221",username = "ccen",password = "ccen")
http_client.call("getinfo")
