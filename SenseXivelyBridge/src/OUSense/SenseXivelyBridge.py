'''
Created on Sep 23, 2013

@author: akb235
'''

import re
import time
import http.server
import socketserver
import xively
import datetime
import requests
from urllib.parse import parse_qs
from OUSense import PyRSS2Gen


HOST_NAME = 'localhost'
PORT_NUMBER = 8080 # Maybe set this to 9000.

XIVELY_FEED_URL = 'https://xively.com/feeds/'

#OU_Distance API Key
#XIVELY_API_KEY = 'HE0YpJ81kV6qf0u73006JNRQEMUJLT9LZNuxbemlql8hOcLP'

#BUCL Test Feed API Key
#XIVELY_API_KEY = 'jQJN13Ze9aYEJRq6RMpIyiBtDL0IuoYUCBFdnEXhudfrNuhc'

#IOThub Feed API Key
XIVELY_API_KEY = '5SRGqR6D7H6bkjhdwRuocYpKW0ZSXEzhgzb8U8tl07gESlI4'

class SenseXivelyBridge(http.server.BaseHTTPRequestHandler):

    def getDataStream(self, feed, streamID):
        try:
            datastream = feed.datastreams.get(streamID)
        except:
            datastream = feed.datastreams.create(streamID)
        return datastream
    
    def do_POST(self):
        # Read POST data variables
        length = int(self.headers['content-length'])
        postvars = parse_qs(self.rfile.read(length),keep_blank_values=1)
        dataValue = postvars.get(b'description')[0].decode("utf-8")
        streamID  = postvars.get(b'title')[0].decode("utf-8")
        feedID  = int(postvars.get(b'feed_name')[0].decode("utf-8"))

        try:
            # Initialise Xively API        
            api = xively.XivelyAPIClient(XIVELY_API_KEY)
            feed = api.feeds.get(feedID)
            
            datastream = self.getDataStream(feed, streamID)
            datastream.current_value = dataValue
            datastream.at = datetime.datetime.now()

            datastream.update()
            self.sendRSSResponse(feed, streamID)
        except requests.HTTPError as e:
            print("HTTPError: {0}".format(e))
        except Exception as e:
            print("Uncaught exception: {0}".format(e))
            raise
        else:
            print("Updated data stream (%s) to: %s @ %s" % (streamID, datastream.current_value, datastream.at))
            
        
        #http.server.CGIHTTPRequestHandler.do_POST(self)
    
    def sendRSSResponse(self, feed, streamID):
        
        feedURL = XIVELY_FEED_URL + str(feed.id)
        
        dataItems = []
        
        #Retrieve the data items of the feed / data stream
        dataStream = self.getDataStream(feed, streamID)
        dataPoints = list(dataStream.datapoints.history(end=datetime.datetime.now(),duration='1day'))
        for datapoint in dataPoints:
            dataItems.append(PyRSS2Gen.RSSItem(title = 'Feed = {0}, Channel = {1} @ {2}'.format(feed.id, streamID, datapoint.at), 
                                               link = feedURL,
                                               description = str(datapoint.value),
                                               guid = '',
                                               pubDate = datapoint.at))
        
        #Generate RSS document for data stream
        rss = PyRSS2Gen.RSS2(title = 'Xively data feed',
                             link = feedURL,
                             description = 'Data feed generated for Feed = {0}, Channel = {1}'.format(feed.id, streamID),
                             lastBuildDate = datetime.datetime.now(),
                             items = dataItems)
        self.send_response(200)
        self.send_header('Content-type', 'application/rss+xml')
        rss.write_xml(self.wfile)
        
    def do_GET(self):
        try:
            feedID = re.search('xively/(.+?)_(.+?)\.rss', self.path).group(1)
            streamID = re.search('xively/(.+?)_(.+?)\.rss', self.path).group(2)
            print("Reading FeedName = %s, Channel = %s" % (feedID, streamID))
    
            api = xively.XivelyAPIClient(XIVELY_API_KEY)
            feed = api.feeds.get(feedID)
            self.sendRSSResponse(feed, streamID)
        except requests.HTTPError as e:
            print("HTTPError({0}): {1}".format(e.code, e.reason))
            
        
        
        
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