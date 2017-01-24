# Version 1: just listen to Twitter
from __future__ import absolute_import, print_function

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from time import sleep

#Version 2: call the bridge from here

import sys
sys.path.insert(0, '/usr/lib/python2.7/bridge/')

#from bridgeclient import BridgeClient as bridgeclient
#goBridge = bridgeclient()


#Check time
from datetime import datetime
now = datetime.now();
closetime = now.replace(hour=17, minute = 05, second=0, microsecond=0)
print(closetime)

import logging
#logging.basicConfig(filename='twitterblink.log',filemode='w', level=logging.DEBUG)
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you after
consumer_key="pr13t2gmj8jFo0Har8CvUSt9Z"
consumer_secret="ZT9X2ZJYw2Wlr4D9L84g7vMVRUB1humUSa2cy3W352gC7QCVSG"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="2190622657-MU2mA5QNqCwjoR7pqzt4nmSaKyRqNcDe0cAjGCc"
access_token_secret="7LnuWchuwEbsliDRJeBMGRioBx2gFtfeqgJwXxZR0wCzF"

# These are the three hashtags to search in Twitter
# Hashtag 1 is for installation
# Hashtag 2 is for medium impact
# Hashtag 3 is for high impact

hashtag1 = '#moobeatonarduino'
hashtag2 = '#iphonegames'
hashtag3 = '#androidgames'
translateHashtag1 = hashtag1.translate(None,'!@#$')
translateHashtag2 = hashtag2.translate(None,'!@#$')
translateHashtag3 = hashtag3.translate(None,'!@#$')

hashtag1Counter = 0;
hashtag2Counter = 0;
hashtag3Counter = 0;
class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    def on_status(self, status):
        global hashtag1Counter
        global hashtag2Counter
        global hashtag3Counter
        global now
        global closetime
        hashtag = status.entities['hashtags']
        while now < closetime:
            now = datetime.now()
            for value in hashtag:            
                if translateHashtag1 in value['text'].lower():
                    #goBridge.put('go', '1')
                    sleep(0.1)
                elif translateHashtag2 in value['text'].lower():
                    if hashtag2Counter < 11:
                        print(hashtag2+' has been tweeted')
                        hashtag2Counter += 1
                        print(hashtag2Counter)                    
                        sleep(0.5)
                    else: 
                        print("#goBridge.put('go', '2')")
                        hashtag2Counter = 0                
                elif translateHashtag3 in value['text'].lower():
                    if hashtag3Counter < 21:
                        print(hashtag3+' has been tweeted')
                        hashtag3Counter += 1
                        print(hashtag3Counter)
                        sleep(0.5)
                    else:
                        print("#goBridge.put('go', '3')")
                        hashtag3Counter = 0
                
            return True
        print("Close time!")
        print("#goBridge.put('go',9)")
        raw_input("Turn off the lights, please. It is closed until tomorrow")        

    #def on_data(self, data):
    #    print(data.text.encode('utf-8'))
    #    return True

    def on_error(self, status):
        print(status)
        logging.warning('Get on_error %s', status)
        return True
    def on_timeout(self):
        print('Timeout')
        logging.warning('Get on_timeout')
        return True
    def on_disconnect(self, notice):
        """Called when twitter sends a disconnect notice
    
        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        """
        logging.warning('Get on_disconnect')
        return True

if __name__ == '__main__':
    while True:
        try:
            #logging.debug('Entetered main if')
            l = StdOutListener()
            auth = OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)

            stream = Stream(auth, l, timeout=30)
            stream.filter(track=[hashtag1, hashtag2, hashtag3])
        except Exception as e:
            print("Error interruption %s" % e)
            logging.warning('Entered Exception %s' % e)
            sleep(4)
            continue
