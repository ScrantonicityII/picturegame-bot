import json
import os
import praw
from const import *
from . import Logger


def initialValuesFromSubreddit(subreddit):
    '''Pull the current subreddit status from Reddit if it is not held on file'''

    initialValues = {}
    for submission in subreddit.new(limit=5):
        if TITLE_PATTERN.match(submission.title):
            initialValues["roundNumber"] = int(submission.title.split()[1].strip(']'))
            initialValues["roundId"] = submission.id
            initialValues["currentHost"] = submission.author.name
            initialValues["unsolved"] = submission.link_flair_text == UNSOLVED_FLAIR
            break
    return initialValues


def importData(state):
    '''Import subreddit status from file, or generate new'''

    if not os.path.isfile("data/data.json"):
        Logger.log("Generating data.json")
        initialValues = initialValuesFromSubreddit(state.subreddit)
        exportData(initialValues)
        return initialValues

    Logger.log("Loading data from data.json")
    with open("data/data.json") as dataFile:
        data = json.loads(dataFile.read())
        currentRoundSubmission = praw.models.Submission(state.reddit, data["roundId"])
        data["unsolved"] = currentRoundSubmission.link_flair_text == UNSOLVED_FLAIR
        return data


def exportData(data):
    '''Export subreddit status to file'''

    Logger.log("Writing data to data.json")
    with open("data/data.json", 'w') as dataFile:
        dataFile.write(json.dumps(data))


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
