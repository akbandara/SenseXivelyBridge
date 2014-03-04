'''
Created on Sep 23, 2013

@author: akb235
'''

import time
import http.server
import socketserver
import xively
import datetime
import requests
import argparse
from urllib.parse import parse_qs
from OUSense import PyRSS2Gen
import threading

import urllib.request
import urllib.parse
import json
import configparser
import os.path 
import uuid
import hmac
CONFIG_FILE = os.path.expanduser("~/.sense_xively.config")

HOST_NAME = 'localhost'
PORT_NUMBER = 8080 # Maybe set this to 9000.

XIVELY_FEED_URL = 'https://xively.com/feeds/'

#OU_Distance API Key
#XIVELY_API_KEY = 'HE0YpJ81kV6qf0u73006JNRQEMUJLT9LZNuxbemlql8hOcLP'

#BUCL Test Feed API Key
#XIVELY_API_KEY = 'jQJN13Ze9aYEJRq6RMpIyiBtDL0IuoYUCBFdnEXhudfrNuhc'

#IOThub Feed API Key
XIVELY_READ_API_KEY = '5SRGqR6D7H6bkjhdwRuocYpKW0ZSXEzhgzb8U8tl07gESlI4'
XIVELY_UPDATE_API_KEY = 'fsPGDjvqoL3WIwHG9oAbb4OfiXKfS6zzXJea0e3REu0qH3e3'

XIVELY_MASTER_API_KEY = 'WEGSMT5oECSICidhqSB76S7m7eiPv4yxl9sIrUfpetrCaVnK'
SENSE_PRODUCT_CODE = 'oX_o7uPqUie-07wBi4m0'

# http://stackoverflow.com/ques'WEGSMT5oECSICidhqSB76S7m7eiPv4yxl9sIrUfpetrCaVnK'tions/17250056/xively-how-to-activate-a-device-with-the-python-api

def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'mood' in config:
        mood_api = xively.XivelyAPIClient(config['mood']['device_api_key'])
        mood_feed = mood_api.feeds.get(config['mood']['feed_id'])
        print (time.asctime(), "Opened device with feedID {}".format(config['mood']['feed_id']))
        return mood_api, mood_feed
    raise EnvironmentError('Invalid config file {}'.format(CONFIG_FILE))

def create_mood_device():
    mood_device_serial_number = uuid.uuid1()
    sn = mood_device_serial_number.hex
    master_api = xively.XivelyAPIClient(XIVELY_MASTER_API_KEY)
    master_client = xively.Client(XIVELY_MASTER_API_KEY)

    # create the device
    device_data = {'devices': [{'serial': sn}]}
    response = master_client.post('/v2/products/{}/devices'.format(SENSE_PRODUCT_CODE), data=device_data)

    # find the just-created device
    senseboards = master_client.get('/v2/products/{}/devices?per_page=1000'.format(SENSE_PRODUCT_CODE)).json()['devices']
    mood_voter = [s for s in senseboards if s['serial'] == sn][0]

    #activate the device
    response = master_client.get('/v2/devices/{}/activate'.format(mood_voter['activation_code'])).json()
    mood_device_api_key = response['apikey']
    mood_device_feed_id = response['feed_id']

    config = configparser.ConfigParser()
    config['mood'] = {'device_api_key': mood_device_api_key, 'feed_id': mood_device_feed_id}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    print (time.asctime(), "Created new device {} with feedID {}".format(mood_device_serial_number, mood_device_feed_id))


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
        postAction = postvars.get(b'action')[0].decode("utf-8")
        streamID  = postvars.get(b'channel')[0].decode("utf-8")
        # feedID  = int(postvars.get(b'feed_name')[0].decode("utf-8"))
        print("Received Request %s - %s" % (postAction, streamID))
        
        try:
            # Initialise Xively API        
            if (postAction == 'load'):
                # api = xively.XivelyAPIClient(XIVELY_READ_API_KEY)
                # feed = api.feeds.get(feedID)
                duration = postvars.get(b'duration')[0].decode("utf-8")
                self.sendRSSResponse(feed, streamID, duration)

            elif (postAction == 'update'):
                # api = xively.XivelyAPIClient(XIVELY_UPDATE_API_KEY)
                # feed = api.feeds.get(feedID)
                dataValue = postvars.get(b'value')[0].decode("utf-8")
                datastream = self.getDataStream(feed, streamID)
                datastream.current_value = dataValue
                datastream.at = datetime.datetime.now()
                datastream.update()
                # threading.Thread(target=datastream.update).start()
                self.sendRSSResponse(feed, streamID, '1minute')
            else:
                self.sendRSSResponse(feed, streamID, '1minute')
                
        except requests.HTTPError as e:
            print("HTTPError: {0}".format(e))
        except Exception as e:
            print("Uncaught exception: {0}".format(e))
            raise
        else:
            if (postAction == 'update'):
                print("Updated data stream (%s) to: %s @ %s" % (streamID, datastream.current_value, datastream.at))
            elif (postAction == 'load'):
                print("Loaded data stream (%s) for duration = %s" % (streamID, duration))
            
        
        #http.server.CGIHTTPRequestHandler.do_POST(self)
    
    def sendRSSResponse(self, feed, streamID, valueRange):
        
        feedURL = XIVELY_FEED_URL + str(feed.id)
        
        dataItems = []
        
        #Retrieve the data items of the feed / data stream
        dataStream = self.getDataStream(feed, streamID)
        dataPoints = list(dataStream.datapoints.history(end=datetime.datetime.now(),duration=valueRange))
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
        self.end_headers()
        rss.write_xml(self.wfile)
        
#     def do_GET(self):
#         try:
#             feedID = re.search('xively/(.+?)_(.+?)\.rss', self.path).group(1)
#             streamID = re.search('xively/(.+?)_(.+?)\.rss', self.path).group(2)
#             print("Reading FeedName = %s, Channel = %s" % (feedID, streamID))
#     
#             api = xively.XivelyAPIClient(XIVELY_API_KEY)
#             feed = api.feeds.get(feedID)
#             self.sendRSSResponse(feed, streamID)
#         except requests.HTTPError as e:
#             print("HTTPError({0}): {1}".format(e.code, e.reason))

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Host and port settings")
    parser.add_argument('-s', '--server', help='Name/IP for SenseXivelyBridge host server')
    parser.add_argument('-p', '--port', type=int, help='Port number for SenseXivelyBridge host server')
    args = parser.parse_args()
    if args.server:
        HOST_NAME = args.server
    if args.port:
        PORT_NUMBER = args.port
    
    try:
        api, feed = read_config()
    except EnvironmentError:
        create_mood_device()
        api, feed = read_config()

    server_class = socketserver.TCPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), SenseXivelyBridge)
    print (time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print (time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
