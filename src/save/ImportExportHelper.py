import json
import os

import praw

from .. import config
from ..const import TITLE_PATTERN, UNSOLVED_FLAIR

from ..actions.Retry import retry
from ..reddit import Wiki

from . import Logger


@retry
def getRoundWonTime(submission, botName):
    submission.comments.replace_more(limit = 0)
    for comment in submission.comments.list():
        if comment.author is not None and \
            comment.author.name.lower() == botName and \
            comment.body.strip().startswith("Congratulations"):
            return comment.created_utc

    # If we can't find anything (e.g. if it's abandoned) just use the submitted time of the post
    return submission.created_utc


@retry
def getRoundStatus(submission, botName):
    data = {}
    if submission.author is None or submission.banned_by is not None:
        # If the ongoing round has been deleted then immediately start listening for new ones
        data["unsolved"] = False
        data["roundWonTime"] = submission.created_utc
    else:
        data["unsolved"] = submission.link_flair_text == UNSOLVED_FLAIR
        if not data["unsolved"]: # make sure we know when the previous round was won
            data["roundWonTime"] = getRoundWonTime(submission, botName)

    return data


@retry
def importData(subreddit):
    '''Pull the current subreddit status from Reddit'''

    botName = config.getKey("botName")

    roundNumber = 0
    roundId = ""
    currentHost = ""
    postTime = 0

    for submission in subreddit.new(limit=5):
        if submission.author is not None and submission.banned_by is None and \
            submission.link_flair_text is not None and \
            TITLE_PATTERN.match(submission.title):

            roundNumber = int(
                submission.title[submission.title.index(' ') + 1 : submission.title.index(']')])
            roundId = submission.id
            currentHost = submission.author.name
            postTime = submission.created_utc
            unsolved = submission.link_flair_text == UNSOLVED_FLAIR

            if not unsolved:
                roundId = None
                roundNumber += 1 # Look for the NEXT round if it's over

            break

    return (roundNumber, roundId, currentHost, postTime)


def exportLeaderboard(subreddit, leaderboard):
    Logger.log("Exporting leaderboard to subreddit")
    Wiki.exportLeaderboard(subreddit, leaderboard)

    Logger.log("Backing up leaderboard to leaderboard.json", 'd')
    with open("data/leaderboard.json", 'w') as leaderboardFile:
        leaderboardFile.write(json.dumps(leaderboard))


def loadCachedLeaderboardStats(username):
    leaderboardData = {}

    with open("data/leaderboard.json") as leaderboardFile:
        leaderboardData = json.loads(leaderboardFile.read())

    if username in leaderboardData:
        return leaderboardData[username]


def loadOrGenerateConfig():
    if not os.path.isfile(config.FileName):
        Logger.log("First time use, generating config.json")
        config.generateConfig()

    Logger.log("Loading config.json")
    config.loadConfig()
