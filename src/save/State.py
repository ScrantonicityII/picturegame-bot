from copy import deepcopy

from . import ImportExportHelper
import praw
from const import *
from . import Logger

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    instance = None
    reddit = None
    subreddit = None
    mods = None
    config = None

    def __init__(self):
        if not State.instance:
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
        return self.instance[name]

    def setState(self, values):
        for key in values.keys():
            self.instance[key] = values[key]
        ImportExportHelper.exportData(self.instance)

    def awardWin(self, username, comment):
        leaderboard = deepcopy(self.leaderboard)
        if username in leaderboard:
            leaderboard[username]["wins"] += 1
            leaderboard[username]["rounds"].append(self.roundNumber)
        else:
            leaderboard[username] = {
                    "wins": 1,
                    "rounds": [self.roundNumber]
                    }

        self.setState({
            "roundNumber": self.roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "leaderboard": leaderboard,
            "roundWonTime": comment.created_utc
            })

