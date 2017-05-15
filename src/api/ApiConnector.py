import json
import requests

import config
from actions.Retry import retry
from save import Logger


@retry
def tryRequest(state, method, *args):
    while True:
        if method(state.apiSessionToken, *args):
            return
        else:
            if not login(state):
                return


def login(state):
    username, password = config.getKey("username"), config.getKey("password")
    
    request = requests.post(config.getKey("pgApiUrl") + "/login", 
            data = json.dumps({ "username": username, "password": password }),
            headers = { "Content-Type": "application/json" })

    if request.status_code == 401:
        print("Failed to get auth token for PG API - check username and password")
        return False

    response = json.loads(request.text)
    state.apiSessionToken = response["token"]
    return True


def post(token, roundNumber, submission):
    roundData = {
        "hostName": submission.author.name,
        "permalink": submission.permalink,
        "postTime": submission.created_utc,
        "url": submission.url,
    }

    request = requests.post(config.getKey("pgApiUrl") + "/rounds/" + str(roundNumber),
            data = json.dumps(roundData),
            headers = {
                "Content-Type": "application/json",
                "X-Picturegame-Session": token,
            })

    if request.status_code == 401:
        # Session token must have expired, time for a new one
        return False

    if request.status_code != 200:
        # Probably a 500, shouldn't ever happen unless there's API downtime
        Logger.log("HTTP status code {} while attempting to post round {} to PG API".format(request.status_code, roundNumber), 'e')

    else:
        Logger.log("Successfully pushed round {} to the PG API".format(roundNumber))

    return True


def put(token, roundNumber, winningComment):
    roundData = {
        "winTime": winningComment.created_utc,
        "winnerName": winningComment.author.name,
    }

    request = requests.put(config.getKey("pgApiUrl") + "/rounds/" + str(roundNumber),
            data = json.dumps(roundData),
            headers = {
                "Content-Type": "application/json",
                "X-Picturegame-Session": token,
            })

    if request.status_code == 401:
        return False

    if request.status_code != 200:
        Logger.log("HTTP status code {} while attempt to put round {} to PG API".format(request.status_code, roundNumber), 'e')

    else:
        Logger.log("Successfully putted round {} to the PG API".format(roundNumber))

    return True
