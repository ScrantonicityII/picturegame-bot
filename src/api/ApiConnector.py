import json
import requests

from .. import config
from ..actions.Retry import retry
from ..save import Logger


def tryRequest(method):
    def _tryRequest(state, *args):
        while True:
            result = method(state.apiSessionToken, *args)
            if result:
                return result
            # If auth fails, we'll just keep trying and failing here
            login(state)

    return _tryRequest


@retry
def login(state):
    username, password = config.getKey("username"), config.getKey("password")

    request = requests.post(config.getKey("pgApiUrl") + "/v1/login",
        data = json.dumps({ "username": username, "password": password }),
        headers = { "Content-Type": "application/json" })

    if request.status_code == 401:
        raise RuntimeError("Failed to get auth token for PG API - check username and password")

    if request.status_code != 200:
        raise RuntimeError("HTTP status code {} while attempting to authenticate with PG API".format(
            request.status_code))

    Logger.log("Successfully authenticated with the PG API", 'i')

    response = json.loads(request.text)
    state.apiSessionToken = response["token"]


@tryRequest
@retry
def post(token, roundNumber, submission):
    roundData = {
        "hostName": submission.author.name,
        "permalink": submission.permalink,
        "postTime": submission.created_utc,
        "postUrl": submission.url,
    }

    request = requests.post(config.getKey("pgApiUrl") + "/v1/rounds/" + str(roundNumber),
        data = json.dumps(roundData),
        headers = {
            "Content-Type": "application/json",
            "X-Picturegame-Session": token,
        })

    if request.status_code == 401:
        # Session token must have expired, time for a new one
        return False

    if request.status_code != 200:
        # This will trigger actionWithRetry, unless it's a 400. 400 should NEVER happen as we'll always
        # be sending good data
        raise RuntimeError("HTTP status code {} while attempting to post round {} to PG API".format(
            request.status_code, roundNumber))

    else:
        Logger.log("Successfully pushed round {} to the PG API".format(roundNumber), 'i')

    return True


@tryRequest
@retry
def put(token, roundNumber, winningComment):
    '''Return the response from a PUT request if it's successful.
    Return None if auth fails, and raise an exception for any other non-200 responses
    '''

    roundData = {
        "winTime": winningComment.created_utc,
        "winnerName": winningComment.author.name,
    }

    request = requests.put(config.getKey("pgApiUrl") + "/v1/rounds/" + str(roundNumber),
        data = json.dumps(roundData),
        headers = {
            "Content-Type": "application/json",
            "X-Picturegame-Session": token,
        })

    if request.status_code == 401:
        return False

    if request.status_code != 200:
        raise RuntimeError("HTTP status code {} while attempt to put round {} to PG API".format(
            request.status_code, roundNumber))

    else:
        Logger.log("Successfully putted round {} to the PG API".format(roundNumber))

    return json.loads(request.text)

@tryRequest
@retry
def delete(token, roundNumber):
    request = requests.delete(config.getKey("pgApiUrl") + "/v1/rounds/" + str(roundNumber),
        headers = {
            "X-Picturegame-Session": token,
        })

    if request.status_code == 401:
        return False

    if request.status_code != 200:
        raise RuntimeError("HTTP status code {} while attempting to delete round {}".format(
            request.status_code, roundNumber))

    else:
        Logger.log("Successfully deleted round {} from PG API".format(roundNumber))

    return True
