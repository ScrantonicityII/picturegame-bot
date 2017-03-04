import json
import requests

from const import PG_API_URL
from save import Logger

def tryRequest(state, method, *args):
    while True:
        if method(state.apiSessionToken, *args):
            return
        else:
            if not login(state):
                return


def login(state):
    username, password = state.config["username"], state.config["password"]
    
    request = requests.post(PG_API_URL + "/login", 
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

    request = requests.post(PG_API_URL + "/rounds/" + str(roundNumber),
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
        Logger.log("HTTP status code {} while attempting to post round {} to PG API".format(request.status_code, roundNumber))

    else:
        Logger.log("Successfully pushed round {} to the PG API".format(roundNumber))

    return True


def put(token, roundNumber, winningComment):
    roundData = {
        "winTime": winningComment.created_utc,
        "winnerName": winningComment.author.name,
    }

    request = requests.put(PG_API_URL + "/rounds/" + str(roundNumber),
            data = json.dumps(roundData),
            headers = {
                "Content-Type": "application/json",
                "X-Picturegame-Session": token,
            })

    if request.status_code == 401:
        return False

    if request.status_code != 200:
        Logger.log("HTTP status code {} while attempt to put round {} to PG API".format(request.status_code, roundNumber))

    else:
        Logger.log("Successfully putted round {} to the PG API".format(roundNumber))

    return True
