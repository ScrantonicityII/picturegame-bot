import json
import logging
import os

import praw

from ..const import TITLE_PATTERN, UNSOLVED_FLAIR

from ..actions.Retry import retry
from ..reddit import Wiki


@retry
def initialValuesFromSubreddit(subreddit, botName):
    '''Pull the current subreddit status from Reddit if it is not held on file'''

    initialValues = {}
    for submission in subreddit.new(limit=5):
        if submission.author is not None and submission.banned_by is None and \
            submission.link_flair_text is not None and \
            TITLE_PATTERN.match(submission.title):

            initialValues["roundNumber"] = int(
                submission.title[submission.title.index(' ') + 1 : submission.title.index(']')])
            initialValues["roundId"] = submission.id
            initialValues["currentHost"] = submission.author.name
            initialValues["unsolved"] = submission.link_flair_text == UNSOLVED_FLAIR

            if not initialValues["unsolved"]:
                initialValues["roundWonTime"] = getRoundWonTime(submission, botName)
                initialValues["roundNumber"] += 1 # Look for the NEXT round if it's over

            break

    return initialValues


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


def importData(state):
    '''Import subreddit status from file, or generate new'''

    if not os.path.isfile("data/data.json"):
        logging.info("Generating new data.json")

        initialValues = initialValuesFromSubreddit(state.subreddit, state.config.getlower("botName"))
        exportData(initialValues)

        return initialValues

    logging.info("Loading data from data.json")
    data = {}
    with open("data/data.json") as dataFile:
        data = json.loads(dataFile.read())

    currentRoundSubmission = praw.models.Submission(state.reddit, data["roundId"])

    roundStatus = getRoundStatus(currentRoundSubmission, state.config.getlower("botName"))
    data["unsolved"] = roundStatus["unsolved"]
    data["roundWonTime"] = roundStatus.get("roundWonTime", None)

    exportData(data)
    return data


def exportData(data):
    logging.debug("Exporting data to data.json")
    with open("data/data.json", 'w') as dataFile:
        dataFile.write(json.dumps(data))


def exportLeaderboard(subreddit, leaderboard):
    logging.info("Exporting leaderboard to subreddit")
    Wiki.exportLeaderboard(subreddit, leaderboard)

    logging.debug("Backing up leaderboard to leaderboard.json")
    with open("data/leaderboard.json", 'w') as leaderboardFile:
        leaderboardFile.write(json.dumps(leaderboard))


def loadCachedLeaderboardStats(username):
    leaderboardData = {}

    with open("data/leaderboard.json") as leaderboardFile:
        leaderboardData = json.loads(leaderboardFile.read())

    if username in leaderboardData:
        return leaderboardData[username]
