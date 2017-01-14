from copy import deepcopy

from . import ImportExportHelper
import praw
from const import *

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    instance = None
    reddit = None
    subreddit = None
    mods = None

    def __init__(self):
        if not State.instance:
            self.reddit = praw.Reddit(SCRIPT_NAME)
            self.subreddit = self.reddit.subreddit(SUBREDDIT_NAME)
            self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))
            self.instance = ImportExportHelper.import_data(self)

    def __getattr__(self, name):
        if name == "reddit":
            return self.reddit
        if name == "subreddit":
            return self.subreddit
        return self.instance[name]

    def setState(self, values):
        for key in values.keys():
            self.instance[key] = values[key]
        ImportExportHelper.export_data(self.instance)

    def awardWin(self, username):
        leaderboard = deepcopy(self.leaderboard)
        if username in leaderboard:
            leaderboard[username].wins += 1
            leaderboard[username].rounds.append(self.roundNumber)
        else:
            leaderboard[username] = {
                    "wins": 1,
                    "rounds": [self.roundNumber]
                    }

        self.setState({
            "roundNumber": self.roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "leaderboard": leaderboard
            })

