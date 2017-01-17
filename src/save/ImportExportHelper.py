import json
import os
import praw
from const import *
from . import Logger
from reddit import Wiki


def initialValuesFromSubreddit(subreddit, botName):
    '''Pull the current subreddit status from Reddit if it is not held on file'''

    initialValues = {}
    for submission in subreddit.new(limit=5):
        if TITLE_PATTERN.match(submission.title):
            initialValues["roundNumber"] = int(submission.title.split()[1].strip(']'))
            initialValues["roundId"] = submission.id
            initialValues["currentHost"] = submission.author.name
            initialValues["unsolved"] = submission.link_flair_text == UNSOLVED_FLAIR

            if not initialValues["unsolved"]:
                initialValues["roundWonTime"] = getRoundWonTime(submission, botName)

            break

    return initialValues


def getRoundWonTime(submission, botName):
    for comment in submission.comments.list():
        if comment.author.name == botName and comment.body.strip().startswith("Congratulations"):
            return comment.created_utc


def importData(state):
    '''Import subreddit status from file, or generate new'''

    if not os.path.isfile("data/data.json"):
        Logger.log("Generating new data.json")

        initialValues = initialValuesFromSubreddit(state.subreddit, state.config["botName"])
        exportData(initialValues)

        return initialValues

    Logger.log("Loading data from data.json")
    data = {}
    with open("data/data.json") as dataFile:
        data = json.loads(dataFile.read())

    currentRoundSubmission = praw.models.Submission(state.reddit, data["roundId"])
    data["unsolved"] = currentRoundSubmission.link_flair_text == UNSOLVED_FLAIR

    if not data["unsolved"]: # make sure we know when the previous round was won
        data["roundWonTime"] = getRoundWonTime(currentRoundSubmission, state.config["botName"])

    exportData(data)
    return data


def exportData(data):
    Logger.log("Exporting data to data.json")
    with open("data/data.json", 'w') as dataFile:
        dataFile.write(json.dumps(data))


def exportLeaderboard(subreddit, leaderboard):
    Logger.log("Exporting leaderboard to subreddit")
    Wiki.exportLeaderboard(subreddit, leaderboard)

    Logger.log("Backing up leaderboard to leaderboard.json")
    with open("data/leaderboard.json", 'w') as leaderboardFile:
        leaderboardFile.write(json.dumps(leaderboard))


def loadOrGenerateConfig():
    if not os.path.isfile("data/config.json"):
        Logger.log("First time use, generating config.json")

        config = {}
        config["scriptName"] = input("Enter script name (the same as in praw.ini): ")
        config["botName"] = input("Enter the reddit username of the bot (case sensitive): ")
        config["subredditName"] = input("Enter the name of the subreddit (case sensitive): ")

        with open("data/config.json", 'w') as configFile:
            configFile.write(json.dumps(config))

        return config

    Logger.log("Loading config.json")
    with open("data/config.json") as configFile:
        return json.loads(configFile.read())
