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


def import_data(state):
    '''Import subreddit status from file, or generate new'''

    if not os.path.isfile("data/data.json"):
        Logger.log("Generating data.json")
        initialValues = initialValuesFromSubreddit(state.subreddit)
        export_data(initialValues)
        return initialValues

    Logger.log("Loading data from data.json")
    with open("data/data.json") as data_file:
        data = json.loads(data_file.read())
        currentRoundSubmission = praw.models.Submission(state.reddit, data["roundId"])
        data["unsolved"] = currentRoundSubmission.link_flair_text == UNSOLVED_FLAIR
        return data


def export_data(data):
    '''Export subreddit status to file'''

    Logger.log("Writing data to data.json")
    with open("data/data.json", 'w') as data_file:
        data_file.write(json.dumps(data))
