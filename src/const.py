import re

SCRIPT_NAME = "pg-bot"

BOT_NAME = "AutoProvium"
SUBREDDIT_NAME = "PGProvium"

TITLE_PATTERN = re.compile("^\[round \d+\]", re.I) # ignore case
