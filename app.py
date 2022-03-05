import tweepy
import os
import json
import time
import logging
import gc

logging.basicConfig(level=logging.INFO)

from decouple import config
from datetime import datetime, timedelta, timezone
import datetime

consumer_key = config('TWITTER_CONSUMER_KEY')
consumer_secret = config('TWITTER_CONSUMER_SECRET')
access_token = config('TWITTER_ACCESS_TOKEN')
access_token_secret = config('TWITTER_ACCESS_TOKEN_SECRET')

now = datetime.datetime.now()
current_date_time = now.strftime("%m_%d_%Y-%H_%M_%S")

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

    i = 0
    count = 200
    sleep_secs = 4  # Implementing sleep due to Twitter's rate limit, 5s seems to be the perfect delay

    while True:
        try:
            i += 1
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
            if (i % count == 0):
                print(f'Iterated #{i} status Tweets, collected {len(all_replies)} Tweet replies so far, sleeping for {sleep_secs} seconds')
                time.sleep(sleep_secs)

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

  earliest_tweet = tweets_with_replies[-1].id

  del tweets_with_replies
  gc.collect()

  mentioned_tweets_count = downloadMentionedTweets(screen_name, earliest_tweet, data_dir, startDate, endDate)

  logging.info("Saved all mentioned tweets")

  return tweets_with_replies

def limit_handled(cursor):
    while True:
        try:
            yield next(cursor)
        except tweepy.TooManyRequests as e:
            time.sleep(15 * 60)
        except tweepy.errors.TweepyException as e:
            time.sleep(60)
        except StopIteration:
            break

def downloadMentionedTweets(screen_name, tweet_id, data_dir, startDate, endDate, count=200):
    '''Function which returns the mentioned Tweets of a particular brand, given a specific start date'''
    if type(startDate) is str:
        startDate = datetime.datetime(int(startDate.split('-')[0]), int(startDate.split('-')[1]), int(startDate.split('-')[2]), tzinfo=timezone(offset=timedelta()))
        endDate = datetime.datetime(int(endDate.split('-')[0]), int(endDate.split('-')[1]), int(endDate.split('-')[2]), tzinfo=timezone(offset=timedelta()))
    logging.info(f"Downloading mentioned tweets for {screen_name} from {startDate} to {endDate}")
    mentionedTweets = []
    i = 0  # Pausing on every 200 Tweets (maximum count for Tweet retrievable)
    sleep_secs = 4
    # 180 requests for every 15 minutes, which brings to 5 seconds for every request, which means that it's more effective to sleep 4 seconds, under the assumption there is a 1s processing time for every request
    # Not much justification towards why choosing this sleep value, but found that it works quite well
    # Works quite well
    save_filename = f'saving_mentioned_tweets_{screen_name}_{current_date_time}.json'
    save_filepath = os.path.join(data_dir, save_filename)

    if save_filename not in os.listdir(data_dir):
        # If Tweets json file not available, create the data file
        with open(save_filepath, 'w') as f:
            f.write('')

    for status in limit_handled(tweepy.Cursor(api.search_tweets, q='@{}'.format(screen_name), tweet_mode='extended', count=count).items()):
        mentionedTweets.append(status)
        i += 1

        if (status.created_at > endDate):
            # Limit retrieving Tweets only start with since Tweet ID, and end at a specific date
            break

        if (i % count == 0):
            # Sleep for every 100 Tweets retrieved, due to Twitter API's rate limits
            time.sleep(sleep_secs)
            print(f'Added mentioned Tweet #{i}, sleeping for {sleep_secs} seconds')

        if (i % 5000 == 0):
            print(status.created_at)
            # Write to file for every 10k JSON objects, then clear array, saves memory this way
            with open(save_filepath, 'a') as f:
                for t in mentionedTweets:
                    if (t.created_at >= startDate) and (t.created_at <= endDate):
                        # Only limit by start and end date ranges
                        f.write(json.dumps(t._json) + '\n')
            mentionedTweets = []
            gc.collect()

    with open(save_filepath, 'a') as f:
        # Write remaining Tweets to file again at the end, before returning
        for t in mentionedTweets:
            if (t.created_at >= startDate) and (t.created_at <= endDate):
                f.write(json.dumps(t._json) + '\n')
    return i