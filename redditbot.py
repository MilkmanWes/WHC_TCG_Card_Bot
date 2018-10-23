#TODO - Parse typo's
#TODO2 - Create more functions (e.g. post building into a function)

import time
import sys
import praw
import re
import urllib.request, urllib.error, urllib.parse
from urllib.parse import quote
import signal, sys
import configparser
from titlecase import titlecase
import os

# Adding the ability to get key variables from a config file
my_scope = os.environ['bot_scope']
config = configparser.ConfigParser()
config.read_file(open('defaults.cfg'))
my_creator_username = config['About']['creator']
my_bot_version = config['About']['version']
my_subbreddits = config['Config']['subreddits']
my_log_parsed_comments = config['Config']['parsed_logfile']

# This string is sent by praw to reddit in accordance to the API rules
my_user_agent = ("REDDIT Bot v%s by /u/%s") % (my_bot_version, my_creator_username)
my_client_id = config['praw']['client_id']
my_secret = config['praw']['secret']
my_username = config['Account']['Username']
my_password = config['Account']['Password']

# This loads the already parsed comments from a backup text file
already_done = []

def main():
    while True:
        global already_done
        ids = []
        r = praw.Reddit(client_id=my_client_id,
                    client_secret=my_secret,
                    password=my_password,
                    user_agent=my_user_agent,
                    username=my_username)
        subreddit = r.subreddit(my_subbreddits)
        if my_scope == 'comments':
            for comment in r.subreddit(my_subbreddits).stream.comments(pause_after=0):
                if comment is None:
                    continue
                with open(my_log_parsed_comments, 'r') as f:
                    if comment.id not in f and comment.id not in already_done and not str(comment.author) == my_username:
                        print('reading %s' % comment.id)
                        print(comment.author)
                        print(comment.body)
                        already_done.append(parser(comment))
                        write_done()
        elif my_scope == 'submissions':
            for submission in r.subreddit(my_subbreddits).stream.submissions():
                if submission is None:
                    continue
                with open(my_log_parsed_comments, 'r') as f:
                    if submission.id not in f and submission.id not in already_done and not str(submission.author) == my_username:
                        print('reading %s' % submission.id)
                        print(submission.author)
                        print(submission.selftext)
                        already_done.append(parser(submission))
                        write_done()
        time.sleep(10)


def parser(message):
    global already_done
    if my_scope == 'comments':
        print('parsing commenmts')
        cards = re.findall("\[\[(.*?)\]\]", message.body.replace("\\",""))
    elif my_scope == 'submissions':
        cards = re.findall("\[\[(.*?)\]\]", message.selftext.replace("\\",""))
    reply = ""
    print("cards:")
    print(cards)
    if len(cards) > 30: cards = cards[0:30]
    for i in set(cards):
        i = titlecase(i)
        i = i.split('/')[0]
        j = quote(i.encode('utf-8'))
        card_id = card_check(i, j)
        if card_id:
            reply += "[%s](https://assets.warhammerchampions.com/card-database/cards/%s.jpg)" % (i, i)
            reply += " - "
            reply += "[Card Database](https://www.warhammerchampions.com/decks-and-packs/card-database/card/%s)" % j
            reply += "\n\n"
    if reply:
        reply += "^^Questions? ^^Message ^^/u/%s ^^- ^^Call ^^cards ^^with ^^[[CARDNAME]] ^^- ^^Format: ^^Image ^^- ^^URL ^^to ^^Card ^^Database" % my_creator_username
        try:
            message.reply(reply)
        except Exception as e: print(str(e))
    return message.id

# Function that checks if the requested card exist and returns the card id (card id is unneccesary 
# for linking since the gatherer will also link the image with it's name, but this is still valid
# to check if the card exists).
def card_check(card, enc_card):
    try:
        # Opens the Gatherer page and looks for the card ID with Regex - Replaces & because it breaks URLs
        with urllib.request.urlopen("https://assets.warhammerchampions.com/card-database/cards/%s.jpg" % enc_card.replace("&", "%26")) as response:
            print('search result: %s' % response.code)       
        return True
    except urllib.error.HTTPError as e:
        if e.code == '403':
            return False

# Function that backs up current parsed comments
def write_done():
    global already_done
    with open(my_log_parsed_comments, "w") as f:
        for i in already_done:
            f.write(str(i) + '\n')

# Function that is called when ctrl-c is pressed. It backups the current parsed comments into a backup file and then quits.
def signal_handler(signal, frame):
    write_done()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    main()
