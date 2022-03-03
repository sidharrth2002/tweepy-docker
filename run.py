import argparse

from app import downloadTimeline

parser = argparse.ArgumentParser()
parser.add_argument("--screen_name", help="Twitter screen name", required=True)
parser.add_argument("--start_date", help="Start date in YYYY-MM-DD format", required=True)
parser.add_argument("--end_date", help="End date in YYYY-MM-DD format", required=True)
parser.add_argument("--data_dir", default="./data", help="Directory to save data", required=True)

args = parser.parse_args()

downloadTimeline(args.screen_name, args.start_date, args.end_date, args.data_dir)