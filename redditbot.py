import time
import sys
import praw
import re
import urllib.request, urllib.error, urllib.parse
from urllib.parse import quote
import signal, sys
import configparser
from titlecase import titlecase
import cloudstorage
from google.appengine.api import app_identity


# Adding the ability to get key variables from a config file
my_scope = sys.argv[1]
#my_scope = 'submissions'
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


# function to actually parse the message out and check it for cards and make te comment
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

#function to gert all bots comments and their parent for skipping
def getMyComments():
    this_comment_ids = []
    for c in r.redditor(my_username).comments.new(limit=None):
        this_comment_ids.append(c.id)
        p = c.parent_id
        this_comment_ids.append(p.replace("t3_", ""))
    return this_comment_ids

already_done = getMyComments()

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
                    if comment.id not in already_done:
                        print('reading %s' % comment.id)
                        print(comment.author)
                        print(comment.body)
                        already_done.append(parser(comment))
        elif my_scope == 'submissions':
            for submission in r.subreddit(my_subbreddits).stream.submissions():
                if submission is None:
                    continue
                with open(my_log_parsed_comments, 'r') as f:
                    if and submission.id not in already_done:
                        print('reading %s' % submission.id)
                        print(submission.author)
                        print(submission.selftext)
                        already_done.append(parser(submission))
        time.sleep(10)

# Function that is called when ctrl-c is pressed. It backups the current parsed comments into a backup file and then quits.
def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    main()
