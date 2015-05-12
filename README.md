# CuriousCat
A simple python script that does automated Twitter based support for events promoted online

This is not great code but just used a bunch of APIs to make it work, suggestions to improve are absolutely welcome.
This code is supposed to run periodically and performs the following tasks

1. It grabs a bunch of tweets with a specific Hashtag, For eg, #savethehacker
2. Analyzes the sentiment of each tweet
3. Based on the sentiment score (positive probability a set of actions are triggered)
4. All matching tweets are bookmarked
5. Highly positive tweets are retweeted
6. Negative tweets are SMSed to a phone number (belonging to the organizer)
7. When tweets are highly negative a phone call is made to the organizer with a specific message
8. Generate simple analysis and send an email to the organizer

Done during @savethehacker 2015 <br/>
Teammate and Idea : @igauravsehrawat
