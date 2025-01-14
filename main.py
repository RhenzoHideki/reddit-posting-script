import json
import praw
import os
import csv
from datetime import datetime, timedelta

def load_config(filename):
    with open(os.path.join('config', filename), 'r') as f:
        return json.load(f)

def load_post_log():
    log_file = os.path.join('config', 'post_log.csv')
    if not os.path.exists(log_file):
        return {}
    log = {}
    with open(log_file, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            log[row['subreddit']] = row['last_posted']
    return log

def update_post_log(subreddit_name):
    log = load_post_log()
    log[subreddit_name] = datetime.now().isoformat()
    log_file = os.path.join('config', 'post_log.csv')
    with open(log_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subreddit', 'last_posted'])
        writer.writeheader()
        for sub, last_posted in log.items():
            writer.writerow({'subreddit': sub, 'last_posted': last_posted})

def initialize_reddit(credentials):
    return praw.Reddit(
        client_id=credentials['client_id'],
        client_secret=credentials['client_secret'],
        user_agent=credentials['user_agent'],
        username=credentials['username'],
        password=credentials['password']
    )

def get_flair_id(subreddit, flair_text):
    if not flair_text:
        return None
    for template in subreddit.flair.link_templates:
        if template['text'] == flair_text:
            return template['id']
    return None

def post_to_subreddit(reddit, subreddit_name, title, images, comment, flair_text, nsfw):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        flair_id = get_flair_id(subreddit, flair_text)
        submission = subreddit.submit_gallery(
            title=title,
            images=[{'image_path': img, 'caption': ''} for img in images],
            nsfw=nsfw,
            flair_id=flair_id
        )
        if comment:
            submission.reply(comment)
        print(f'Successfully posted to r/{subreddit_name}')
    except Exception as e:
        print(f'Error posting to r/{subreddit_name}: {e}')

def can_post_to_subreddit(subreddit_name, interval_days):
    log = load_post_log()
    last_posted = log.get(subreddit_name)
    if not last_posted:
        return True
    if interval_days is None:
        return True
    last_posted_time = datetime.fromisoformat(last_posted)
    next_post_time = last_posted_time + timedelta(days=interval_days)
    return datetime.now() >= next_post_time

def main():
    credentials = load_config('credentials.json')
    subreddits = load_config('subreddits.json')
    content = load_config('content.json')
    
    reddit = initialize_reddit(credentials)
    
    for subreddit, info in subreddits.items():
        interval_days = info.get('interval_days')
        if can_post_to_subreddit(subreddit, interval_days):
            post_to_subreddit(
                reddit,
                subreddit,
                info['titulo'],
                content['images'],
                content['comment'],
                info['flair_text'],
                info.get('nsfw', False)
            )
            update_post_log(subreddit)
        else:
            print(f"Skipping {subreddit}: Minimum interval of {interval_days} days not yet passed.")

if __name__ == "__main__":
    main()
