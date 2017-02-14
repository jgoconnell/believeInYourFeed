#!/usr/bin/env python
# coding: utf-8
import time
import json
import threading

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
USE_GEVENT = False
if USE_GEVENT:
    from gevent.pywsgi import WSGIServer
    from geventwebsocket.handler import WebSocketHandler
else:
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket


class HashTagCount(object):
    def __init__(self):
        self.charge_threshold_secs = 2.0
        self.max_charge = 100.0
        self.max_charge_tweets = 10.0
        self.increment_unit = self.max_charge / self.max_charge_tweets 
        self.decrement = self.increment_unit / 10

        self.last_updated = time.time()
        self.last_charge_level_decay_poll = 0

        self.charge_level = 0.0
        self.count = 0

    def increment(self):
        time_now = time.time()
        time_diff = time_now - self.last_updated
        self.last_updated = time_now

        if self.charge_level < self.max_charge:
            self.charge_level += self.increment_unit 
        if self.charge_level > self.max_charge:
            self.charge_level = self.max_charge 

        self.last_charge_level_decay_poll = 0
        self.count += 1

    def get_value(self):
        time_diff = time.time() - self.last_updated
        if time_diff <= self.charge_threshold_secs:
            return self.charge_level
        else: 
            decay_diff = 0
            if self.last_charge_level_decay_poll != 0:
                decay_diff = time.time() - self.last_charge_level_decay_poll
            else:
                decay_diff = time.time() - self.last_updated
            self.last_charge_level_decay_poll = time.time()
            decay_to_apply = decay_diff * self.decrement
            if self.charge_level > 0:
                self.charge_level -= decay_to_apply
            else:
                self.charge_level = 0.0
            if self.charge_level < 0.0:
                self.charge_level = 0.0
        return self.charge_level


class HashTagCounter(object):
    def __init__(self):
        self.num_clients = 0
        self.hash_tags = ["#starwars", "#trump", "#bestfanarmy", "#apple", "#google", "#love", "#selfie"]
        self.hashtag_index = 0;
        self.hashtag_map = self.get_tag_counter()

    def add_user(self):
        self.hashtag_index = self.num_clients % len(self.hash_tags)
        self.num_clients = self.num_clients + 1
        return self.hash_tags[self.hashtag_index]

    def get_tag_counter(self):
        return dict([(tag, HashTagCount()) for tag in self.hash_tags])
    

class Settings(object):
    consumer_key = "pr13t2gmj8jFo0Har8CvUSt9Z"
    consumer_secret = "ZT9X2ZJYw2Wlr4D9L84g7vMVRUB1humUSa2cy3W352gC7QCVSG"
    access_token="2190622657-MU2mA5QNqCwjoR7pqzt4nmSaKyRqNcDe0cAjGCc"
    access_token_secret="7LnuWchuwEbsliDRJeBMGRioBx2gFtfeqgJwXxZR0wCzF"
    server_port = 6699
    max_clients = 7
    client_poll_interval = 0.5
    KILL_TWEEPY = False


settings = Settings()
tag_counter = HashTagCounter()

class TestTweetListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_status(self, status):
        print("Receieve a tweet from twitter and update the values in a global array? %s" % status)
    def on_data(self, data):
        #print("Got data! %s" % data)
        if settings.KILL_TWEEPY:
            return False
        else:
            #import pdb; pdb.set_trace()
            json_data = json.loads(data)
            if "text" in json_data:
                for tag in tag_counter.hashtag_map.keys():
                    if tag.lower() in json_data["text"].lower():
                        #print("Incrementing count for tag: %s" % tag)
                        tag_counter.hashtag_map[tag].increment()
            #tag_counter.hashtag_map[tag]
            return True

    def on_error(self, status):
        print("Received an error: %s" % status)
        return True

    def on_timeout(self):
        print('Receieved a Timeout from the twitter data service')
        return True

    def on_disconnect(self, notice):
        """Called when twitter sends a disconnect notice
   
        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        """
        print(" Received a  on_disconnect")
        return True

"""

Begin GEVENT STUFF

""" 

class ClientDataPusher(object):
    def __init__(self, ws, tag):
        self.tag = tag
        self.ws = ws
        self.start_pushing()

    def start_pushing(self):
        self.ws.send(self.tag)
        while True:
            time.sleep(settings.client_poll_interval) 
            print("Wake up and send the count to our client")
            data_for_client = {}
            data_for_client["charge_level"] = tag_counter.hashtag_map[self.tag].get_value()
            data_for_client["total_count"] = tag_counter.hashtag_map[self.tag].count
            data_for_client["last_updated"] = tag_counter.hashtag_map[self.tag].last_updated
            data_for_client["tag_name"] = self.tag
            print ("Sending data to client: %s" % data_for_client)
            self.ws.send("%s" % json.dumps(data_for_client))


client_data_pushers = []

def app(environ, start_response):
    ws = environ['wsgi.websocket']
    data = ws.receive()
    if len(client_data_pushers) < settings.max_clients:
        tag = tag_counter.add_user()
        print ("Got a new connectiion on this tag: %s" % tag)
        client_data_pushers.append(ClientDataPusher(ws, tag))
    else:
        ws.close()

"""

END GEVENT stuff

"""


battery_clients = []

class BatteryClient(WebSocket):

    def handleMessage(self):
        print("Got a message from the client, thats weird")
        if not self.active:
            self.active = True
            # Ok, we not using gevent but rather a hackHacky toy implementation so life is difficult now
            #import pdb; pdb.set_trace()
            t = threading.Thread(group=None, target=self.start_pushing);
            t.start()

    def handleConnected(self):
        #import pdb; pdb.set_trace()
        print("Got a new connection from address: %s" % self.address[0])
        if len(battery_clients) >= settings.max_clients:
            print("Too many clients... close the connection")
            self.sendClose()
        else:
            #import pdb; pdb.set_trace()
            for c in battery_clients:
                if c.address[0] == self.address[0]:
                    print("Got another connection from the same address..switch tags!!")
                    c.active = False
                    battery_clients.remove(c)
            self.tag = tag_counter.add_user()
            print ("Assigning this tag to the new connection: %s" % self.tag)
            battery_clients.append(self)
            self.active = False

    def handleClose(self):
        print("Got a closeConnection message...")
        for c in battery_clients:
            if self == c:
                print("Removing batteryClient: %s" % c)
                self.active = False
                battery_clients.remove(self)

    def start_pushing(self):
        print("About to start pushing - send tag to user")
        self.sendMessage(unicode(self.tag))
        while self.active:
            time.sleep(settings.client_poll_interval) 
            print("Wake up and send the count to our client")
            data_for_client = {}
            data_for_client["charge_level"] = tag_counter.hashtag_map[self.tag].get_value()
            data_for_client["total_count"] = tag_counter.hashtag_map[self.tag].count
            data_for_client["last_updated"] = tag_counter.hashtag_map[self.tag].last_updated
            data_for_client["tag_name"] = self.tag
            print ("Sending data to client using sendMessage: %s" % data_for_client)
            self.sendMessage(u"%s" % json.dumps(data_for_client))



def runTweepy():
    l = TestTweetListener()
    auth = OAuthHandler(Settings.consumer_key, Settings.consumer_secret)
    auth.set_access_token(Settings.access_token, Settings.access_token_secret)

    stream = Stream(auth, l, timeout=40000)
    while True: 
        try:
            stream.filter(track=tag_counter.hash_tags)
        except Exception as e:
            print("Uh oh, Tweepy bombed out with an error: %s" % e)
            print("Restart stream filtering...")
            continue


if __name__ == "__main__":

    t = threading.Thread(group=None, target=runTweepy)
    t.daemon=True
    t.start()
    try:
        print("Serving starting up listenening on port: %d" % settings.server_port)
        if USE_GEVENT:
            server = WSGIServer(("", settings.server_port), app,handler_class=WebSocketHandler)
            server.serve_forever()
        else:
            server = SimpleWebSocketServer('', settings.server_port, BatteryClient)
            server.serveforever()
    except KeyboardInterrupt, e:
        print("Receieved Ctrl-C, disconnect the tweepy")
        #stream.disconnect()
        print ("Set all clients to inactive:")
        for c in battery_clients:
            c.active=False
    except Exception, e:
        print("Unknown exception, byebye : %s" % e)
    settings.KILL_TWEEPY = True
