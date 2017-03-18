import json
import os
import praw

import config
from const import *

from . import ImportExportHelper
from . import Logger

from actions.Retry import actionWithRetry
from reddit import Wiki

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    reddit = None
    subreddit = None
    mods = None
    instance = None
    seenComments = None
    seenPosts = None
    commentedRoundIds = None # Dict keys = round ids, values = comment objects
    seenVersion = ""
    # apiSessionToken = ""

    def __init__(self):
        if not os.path.isdir("data"):
            os.mkdir("data")

        if not State.instance:
            Logger.log("Initialising State", 'w')
            self.reddit = praw.Reddit(config.getKey("scriptName"))
            self.subreddit = self.reddit.subreddit(config.getKey("subredditName"))
            actionWithRetry(self.updateMods)
            self.instance = ImportExportHelper.importData(self)
            self.updateVersion()
            self.seenComments = set()
            self.seenPosts = set()
            self.commentedRoundIds = {}

    def updateMods(self):
        self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))

    def __getattr__(self, name):
        if name == "leaderboard":
            return actionWithRetry(Wiki.scrapeLeaderboard, self.subreddit)
        return self.instance[name]

    def setState(self, values):
        for key in values.keys():
            self.instance[key] = values[key]
        ImportExportHelper.exportData(self.instance)

    def awardWin(self, username, comment):
        leaderboard = self.leaderboard
        roundNumber = self.roundNumber
        roundWonTime = actionWithRetry(lambda c: c.created_utc, comment)

        numWins = 0
        rounds = []

        if username in leaderboard:
            numWins = leaderboard[username]["wins"] + 1
            rounds = leaderboard[username]["rounds"] + [roundNumber]
        else:
            numWins = 1
            rounds = [roundNumber]

        leaderboard[username] = {
                "wins": numWins,
                "rounds": rounds
                }

        self.setState({
            "roundNumber": roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "roundWonTime": roundWonTime,
        })

        ImportExportHelper.exportLeaderboard(self.subreddit, leaderboard)

    def updateVersion(self):
        with open("VERSION") as versionFile:
            self.seenVersion = versionFile.read().strip()
