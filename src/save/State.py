import json
import os

from . import ImportExportHelper
import praw
from const import *
from . import Logger
from reddit import Wiki
from actions.Retry import actionWithRetry

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    reddit = None
    subreddit = None
    mods = None
    config = None
    instance = None
    seenComments = None
    seenPosts = None
    commentedRoundIds = None # Dict keys = round ids, values = comment objects

    def __init__(self):
        if not os.path.isdir("data"):
            os.mkdir("data")

        if not State.config:
            Logger.log("Initialising State", 'w')
            self.config = ImportExportHelper.loadOrGenerateConfig()
            self.reddit = praw.Reddit(self.config["scriptName"])
            self.subreddit = self.reddit.subreddit(self.config["subredditName"])
            actionWithRetry(self.updateMods)
            self.instance = ImportExportHelper.importData(self)
            self.seenComments = set()
            self.seenPosts = set()
            self.commentedRoundIds = {}

    def updateMods(self):
        self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))

    def __getattr__(self, name):
        if name == "reddit":
            return self.reddit
        if name == "subreddit":
            return self.subreddit
        if name == "config":
            return self.config
        if name == "mods":
            return self.mods
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
            "roundWinner": {
                "wins": numWins,
                "rounds": rounds
                }
            })

        ImportExportHelper.exportLeaderboard(self.subreddit, leaderboard)
