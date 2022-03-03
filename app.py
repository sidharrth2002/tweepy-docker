import tweepy
import os
import json
import time
import logging

consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

def save_json(filename, obj, data_dir):
    # Writing to JSON
    with open(os.path.join(data_dir, filename), 'w') as f:
        f.write(json.dumps([tweet._json for tweet in obj], indent=4))

def get_replies(tweet_id, user_name, data_dir='./data'):
    replies = tweepy.Cursor(api.search_tweets, q='to:{}'.format(user_name),
                                    since_id=tweet_id, tweet_mode='extended').items()
    all_replies = []
    while True:
        try:
            reply = replies.next()
            if not hasattr(reply, 'in_reply_to_status_id_str'):
                continue
            if reply.in_reply_to_status_id == tweet_id:
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

    return all_replies

def downloadTimeline(screen_name, count, startDate, endDate):
  counter = 0
  results = api.user_timeline(screen_name=screen_name, count=count, include_rts=True, exclude_replies=False)
  tweets = []
  replies = {}
  for tweet in results:
    tweets.append(tweet)
    tweet_replies = get_replies(tweet.id, screen_name)
    replies[tweet.id] = tweet_replies
  save_json(f'{screen_name}_timeline_{counter}.json', tweets)
  save_json(f'{screen_name}_replies_{counter}.json', replies)
  tweets = []
  replies = {}
  counter += 1

  while (results[-1].created_at > startDate):
    logging.info(f'Last tweet collected was created at {results[-1].created_at}, retrieving more')
    results = api.user_timeline(screen_name=screen_name, count=count, max_id=results[-1].id-1, include_rts=True, exclude_replies=False)
    for tweet in results:
      if (tweet.created_at >= startDate):
        tweets.append(tweet)
        tweet_replies = get_replies(tweet.id, screen_name)
        replies[tweet.id] = tweet_replies

    save_json(f'{screen_name}_timeline_{counter}.json', tweets)
    save_json(f'{screen_name}_replies_{counter}.json', replies)
    tweets = []
    replies = {}
    counter += 1

  for tweet in tweets:
    print(f'{tweet.id} | {tweet.text}')