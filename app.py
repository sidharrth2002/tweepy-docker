import tweepy
import os
import json
import time
import logging

logging.basicConfig(level=logging.INFO)

from decouple import config
from datetime import datetime, timedelta, timezone
import datetime

consumer_key = config('TWITTER_CONSUMER_KEY')
consumer_secret = config('TWITTER_CONSUMER_SECRET')
access_token = config('TWITTER_ACCESS_TOKEN')
access_token_secret = config('TWITTER_ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

def save_list_to_json(filename, obj, data_dir):
    # Writing to JSON
    with open(os.path.join(data_dir, filename), 'w') as f:
        f.write(json.dumps([dict(tweet._json) for tweet in obj], indent=4))

def save_obj_to_json(filename, obj, data_dir):
    # Writing to JSON
    with open(os.path.join(data_dir, filename), 'w') as f:
        f.write(json.dumps(obj, indent=4))

def get_replies(tweets, tweet_ids, user_name, data_dir='./data'):
    latest_tweet_id = tweet_ids[-1] + 1
    replies = tweepy.Cursor(api.search_tweets, q='to:{}'.format(user_name),
                                    since_id=latest_tweet_id, tweet_mode='extended', count=200).items()
    all_replies = []
    while True:
        try:
            reply = replies.next()
            if not hasattr(reply, 'in_reply_to_status_id_str'):
                continue
            tweet_id = reply.in_reply_to_status_id
            if reply.in_reply_to_status_id in tweet_ids:
                index = tweet_ids.index(tweet_id)
                if 'replies' not in tweets[index]._json:
                    tweets[index]._json['replies'] = []
                tweets[index]._json['replies'].append(reply._json)
                logging.info("reply of tweet:{}".format(reply.full_text))
                all_replies.append(reply)

        except tweepy.TooManyRequests as e:
            logging.error("Twitter api rate limit reached".format(e))
            time.sleep(60)
            continue

        except tweepy.errors.TweepyException as e:
            logging.error("Tweepy error occured:{}".format(e))
            break

        except tweepy.errors.TwitterServerError as e:
            logging.error("Twitter server error occured:{}".format(e))
            break

        except StopIteration:
            break

        except Exception as e:
            logging.error("Failed while fetching replies {}".format(e))
            break

    return tweets

def downloadTimeline(screen_name, startDate, endDate, data_dir, count=200):
  logging.info(f"Downloading timeline for {screen_name} from {startDate} to {endDate}")
  startDate = datetime.datetime(int(startDate.split('-')[0]), int(startDate.split('-')[1]), int(startDate.split('-')[2]), tzinfo=timezone(offset=timedelta()))
  endDate = datetime.datetime(int(endDate.split('-')[0]), int(endDate.split('-')[1]), int(endDate.split('-')[2]), tzinfo=timezone(offset=timedelta()))
  results = api.user_timeline(screen_name=screen_name, count=count, include_rts=True, exclude_replies=False)
  tweets = []
  tweet_ids = []
  for tweet in results:
    if (tweet.created_at >= startDate) and (tweet.created_at <= endDate):
        tweets.append(tweet)
        tweet_ids.append(tweet.id)
        logging.info(f"Tweet: {tweet.text}")

  while (results[-1].created_at > startDate):
    logging.info(f'Last tweet collected was created at {results[-1].created_at}, retrieving more')
    results = api.user_timeline(screen_name=screen_name, count=count, max_id=results[-1].id-1, include_rts=True, exclude_replies=False)
    for tweet in results:
      if (tweet.created_at >= startDate):
        tweets.append(tweet)
        tweet_ids.append(tweet.id)

  # save only tweets without replies
  save_list_to_json(f'{screen_name}_tweets.json', tweets, data_dir)

  logging.info("Saved all tweets")

  # get replies
  tweets_with_replies = get_replies(tweets, tweet_ids, screen_name, data_dir)

  # save tweets with replies
  save_list_to_json(f'{screen_name}_tweets_replies.json', tweets_with_replies, data_dir)

  logging.info("Saved all tweets with replies")
