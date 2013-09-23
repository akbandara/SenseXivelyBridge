'''
Created on Sep 23, 2013

@author: akb235
'''

import time
import http.server
import socketserver


HOST_NAME = 'dhcp-137-108-49-48.open.ac.uk' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8080 # Maybe set this to 9000.


class SenseXivelyBridge(http.server.CGIHTTPRequestHandler):

    def do_POST(self):
        print("Command = %s" % self.command)
        http.server.CGIHTTPRequestHandler.do_POST(self)
        
    def do_GET(self):
        print("Command = %s" % self.command)
        http.server.CGIHTTPRequestHandler.do_GET(self)
        
        
if __name__ == '__main__':
    server_class = socketserver.TCPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), SenseXivelyBridge)
    print (time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print (time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))