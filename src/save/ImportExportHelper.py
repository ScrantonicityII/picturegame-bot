import json
import os
import re


def initialValuesFromSubreddit(subreddit):
    '''Pull the current subreddit status from Reddit if it is not held on file'''

    initialValues = {}
    regex = re.compile("^\[round \d+\]", re.I) # ignore case
    for submission in subreddit.new(limit=5):
        if regex.match(submission.title):
            initialValues["roundNumber"] = int(submission.title.split()[1].strip(']'))
            initialValues["roundId"] = submission.id
            initialValues["currentHost"] = submission.author.name
            break
    return initialValues


def import_data(subreddit):
    '''Import subreddit status from file, or generate new'''

    if not os.path.isfile("data/data.json"):
        print("First time use, creating data file...")
        initialValues = initialValuesFromSubreddit(subreddit)
        export_data(initialValues)
        return initialValues

    print("Loading previously saved data...")
    with open("data/data.json") as data_file:
        return json.loads(data_file.read())


def export_data(data):
    '''Export subreddit status to file'''

    with open("data/data.json", 'w') as data_file:
        data_file.write(json.dumps(data))
