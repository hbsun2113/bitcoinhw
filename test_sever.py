#!/usr/bin/env python
# coding: utf-8

import pyjsonrpc


class RequestHandler(pyjsonrpc.HttpRequestHandler):

    @pyjsonrpc.rpcmethod
    def add(self, a, b):
        """Test method"""
        return a + b


import socket
print str(123)+" "+socket.gethostbyname("")
# Threading HTTP-Server
http_server = pyjsonrpc.ThreadingHttpServer(
    server_address = ('', 8080),
    RequestHandlerClass = RequestHandler
)
print "Starting HTTP server ..."
print "URL: http://localhost:8080"
#print(help(http_server))
http_server.serve_forever()
