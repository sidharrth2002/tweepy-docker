import json

tweets = json.load(open('/Users/SidharrthNagappan/Downloads/TheDemocrats_tweets_replies.json'))
print(tweets[-1]['id'])