import argparse

from app import downloadMentionedTweets, downloadTimeline

parser = argparse.ArgumentParser()
parser.add_argument("--screen_name", help="Twitter screen name", required=True)
parser.add_argument("--start_date", help="Start date in YYYY-MM-DD format", required=True)
parser.add_argument("--end_date", help="End date in YYYY-MM-DD format", required=True)
parser.add_argument("--data_dir", help="Directory to save data")

args = parser.parse_args()

# downloadTimeline(args.screen_name, args.start_date, args.end_date, args.data_dir)
downloadMentionedTweets(args.screen_name, 1497007436783366150, args.data_dir, args.start_date, args.end_date)