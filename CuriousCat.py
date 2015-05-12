# CuriousCat - A simple python script that does automated Twitter based support for events like Hackathons
# This is not great code but just used a bunch of APIs to make it work, suggestions to improve are absolutely welcome.
# This code is supposed to run periodically and performs the following tasks
# 1. It grabs a bunch of tweets with a specific Hashtag, For eg, #savethehacker
# 2. Analyzes the sentiment of each tweet
# 3. Based on the sentiment score (positive probability a set of actions are triggered)
# 4. All matching tweets are bookmarked
# 5. Highly positive tweets are retweeted
# 6. Negative tweets are SMSed to a phone number (belonging to the organizer)
# 7. When tweets are highly negative a phone call is made to the organizer with a specific message
# 8. Generate simple analysis and send an email to the organizer

# Author : @yeskarthik
# Done during @savethehacker 2015
# Teammate and Idea : @igauravsehrawat

from twilio.rest import TwilioRestClient
import requests
import tweepy
import json
import mandrill
import datetime

TWITTER_HASHTAG = "savethehacker"

SENTIMENT_API_ENDPOINT = "http://text-processing.com/api/sentiment/"
RETWEET_SENTIMENT = 0.65 # change according to your needs Higher the value, more probability that the tweet is positive
SMS_PRIORITY_SENTIMENT = 0.50 # change according to your needs
CALL_PRIORITY_SENTIMENT = 0.40 # change according to your needs
SMS_FROM = "" # Fill this up with your Twilio From number
SMS_TO = "" # Fill this up with the Organizer's number
RPP = 20 # No. of Tweets to grab per run

#Tweepy
TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""
 
#Twilio
TWILIO_ACCOUNT_SID = "" 
TWILIO_AUTH_TOKEN  = ""
TWILIO_SID = ""
TWIML_ENDPOINT = "http://yeskarthik.in/twilio-test.xml" # Host such an XML file with your own custom message

#Mandrill
MANDRILL_API_KEY = ""
FROM_EMAIL_ADDRESS = ""
FROM_EMAIL_NAME = "Hackathon Bot"
TO_EMAIL_ADDRESS = "" 
TO_EMAIL_NAME = "" 

# returns positive sentiment probability of a given text
def findSentiment(text):
  r = requests.post(SENTIMENT_API_ENDPOINT, data={'text': text})
  js = json.loads(r.text)
  return js['probability']['pos']

class TwitterClient:
  def __init__(self):
    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    self.api = tweepy.API(auth)

  def tweets(self, searchTerm):
    results = self.api.search(searchTerm, count=RPP)
    return results

  def favouriteTweet(self, status_id):
    try:
      self.api.create_favorite(status_id)
    except:
      pass # Its probably already favourited

  def retweet(self, status_id):
    try:
      self.api.retweet(status_id)
    except:
      pass # Its probably already retweeted


class TwilioClient:

  def __init__(self):
    self.twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

  def sendSms(self, sms_text):
    print "Sending SMS to " + SMS_TO + sms_text
    message = self.twilio_client.messages.create(body=sms_text,
                  to=SMS_TO,
                  from_=SMS_FROM)
    print message.sid  

  def sendCall(self):
    call = self.twilio_client.calls.create(
            to=SMS_TO, 
            from_=SMS_FROM, 
            url=TWIML_ENDPOINT, 
            method="GET", 
            fallback_method="GET", 
            status_callback_method="GET", 
            record="false") 

    print call.sid
  
class Report:

  def generateReport(self, sentiments, smsPriorityTweets, callPriorityTweets):
    average = reduce(lambda x, y: x + y, sentiments) / len(sentiments)
    results = self.generateAnalysis(average, sentiments, smsPriorityTweets, callPriorityTweets)
    subject = 'Hackathon Bot ' + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + results
    email_text = self.generateEmail(callPriorityTweets, smsPriorityTweets, results)
    self.send_email_internal(FROM_EMAIL_ADDRESS, FROM_EMAIL_NAME, TO_EMAIL_ADDRESS, TO_EMAIL_NAME, subject, email_text)
  
  def generateAnalysis(self, average, sentiments, smsPriorityTweets, callPriorityTweets):
    results = 'Average positive sentiment :' + str("%.3f" % average) + ' out of ' + str(len(sentiments)) 
        + ' tweets. No. of Tweets < ' + str("%.3f" % SMS_PRIORITY_SENTIMENT) + ' is ' + str(len(smsPriorityTweets)) 
        + ' and < ' + str("%.3f" % CALL_PRIORITY_SENTIMENT) + ' is ' + str(len(callPriorityTweets))

    return results

  def generateEmail(self, callPriorityTweets, smsPriorityTweets, results):
    # Of course, in this place I'm going to use a templating library. Generating HTML like this sucks and totally not recommended :P
    priorityTweets = "<h4>Call Priority Tweets: </h4>"
    for each in callPriorityTweets:
      priorityTweets = priorityTweets + "<p>" + each + '</p>'
    
    priorityTweets = priorityTweets + "<h4>SMS Priority Tweets</h4>"
    
    for each in smsPriorityTweets:
      priorityTweets = priorityTweets + "<p>" + each + "</p> <br/>"

    priorityTweets = priorityTweets + "<br/>Thank You,<br/><p>" 
        + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") + "</p><p>Hackathon Bot</p>"
    
    emailText = "<html><body><p>Hello Rescuer, </p>" +  "<br/><strong>" + results + "</strong><br/>" + priorityTweets + "</body></html>"
    return emailText

  def send_email_internal(self, from_address, from_name,to_address, to_name, subject, html):
    m = mandrill.Mandrill(MANDRILL_API_KEY)
    message = {
      "from_email": from_address,
      "from_name": from_name,
      "to" : [
        {
        "email": to_address,
        "name": to_name,
        "type": "to"
        }
      ],
      "subject": subject,
      "html": html
    }
    result = m.messages.send(message)
    assert len(result) == 1
    result0 = result[0]

    return result0

def process(searchTerm):
  sentiments = []
  smsPriorityTweets = []
  callPriorityTweets = []
  call = False
  twilio = TwilioClient()
  twitter = TwitterClient()

  results = twitter.tweets(searchTerm)
  for status in results:
    # Favourite the tweet
    twitter.favouriteTweet(status.id)
    # sanitize the tweet
    text = status.text.encode('ascii', 'ignore') 
    # find the sentiment
    sentiment = findSentiment(text)
    # ignore the RTs
    if text[0:2] == 'RT':
      continue
    print text, ' -- ', "%.3f" % sentiment
    # Retweet the tweet if the sentiment is highly positive
    if sentiment > RETWEET_SENTIMENT:
      twitter.retweet(status.id)

    # send SMS to admins if sentiment is on the negative side
    if sentiment < SMS_PRIORITY_SENTIMENT:
      # add username and sentiment score to the message
      sms_text = '@' + status.user.screen_name + ': ' + text + ' |SS: ' + str("%.3f" % sentiment)
      twilio.sendSms(sms_text)
      smsPriorityTweets = smsPriorityTweets + [sms_text]

      # If highly negative, make sure you send a call about the situation.
      if sentiment < CALL_PRIORITY_SENTIMENT:
        callPriorityTweets = callPriorityTweets + [sms_text]
        call = True     # sendCall()

    sentiments = sentiments + [sentiment]

  # Execute the call
  if call == True:
    twilio.sendCall()

  report = Report()
  report.generateReport(sentiments, smsPriorityTweets, callPriorityTweets)

process(TWITTER_HASHTAG)
