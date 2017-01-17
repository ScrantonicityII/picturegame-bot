import json
import os

from . import ImportExportHelper
import praw
from const import *
from . import Logger
from reddit import Wiki

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    reddit = None
    subreddit = None
    mods = None
    config = None
    instance = None

    def __init__(self):
        if not os.path.isdir("data"):
            os.mkdir("data")

        if not State.config:
            Logger.log("Initialising State", 'w')
            self.config = ImportExportHelper.loadOrGenerateConfig()
            self.reddit = praw.Reddit(self.config["scriptName"])
            self.subreddit = self.reddit.subreddit(self.config["subredditName"])
            self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))
            self.instance = ImportExportHelper.importData(self)

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
            return Wiki.scrapeLeaderboard(self.subreddit)
        return self.instance[name]

    def setState(self, values):
        for key in values.keys():
            self.instance[key] = values[key]
        ImportExportHelper.exportData(self.instance)

    def awardWin(self, username, comment):
        leaderboard = self.leaderboard
        roundNumber = self.roundNumber
        if username in leaderboard:
            leaderboard[username]["wins"] += 1
            leaderboard[username]["rounds"].append(roundNumber)
        else:
            leaderboard[username] = {
                    "wins": 1,
                    "rounds": [roundNumber]
                    }

        self.setState({
            "roundNumber": roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "roundWonTime": comment.created_utc
            })

        ImportExportHelper.exportLeaderboard(self.subreddit, leaderboard)
