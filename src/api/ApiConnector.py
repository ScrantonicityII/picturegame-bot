import json
import logging
import requests

from .. import config
from ..actions.Retry import retry


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
        logging.error("HTTP status code %d while attempting to post round %d to PG API",
            request.status_code, roundNumber)

    else:
        logging.info("Successfully pushed round %d to the PG API", roundNumber)

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
        logging.error("HTTP status code %d while attempt to put round %d to PG API",
            request.status_code, roundNumber)

    else:
        logging.info("Successfully putted round %d to the PG API", roundNumber)

    return True
