import os
import praw

from .. import config

from ..actions.Retry import retry
from ..reddit import utils

from . import ImportExportHelper
from . import Logger

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    class __State:
        def __init__(self):
            Logger.log("Initialising State")
            self.reddit = praw.Reddit(config.getKey("scriptName"))
            self.subreddit = self.reddit.subreddit(config.getKey("subredditName"))
            self.updateMods()
            self.data = ImportExportHelper.importData(self)
            self.updateVersion()
            self.seenComments = set()
            self.seenPosts = set()
            self.commentedRoundIds = {} # keys = round ids, values = comment objects
            self.apiSessionToken = ""

        def updateMods(self):
            self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))

        def updateVersion(self):
            with open("VERSION") as versionFile:
                self.seenVersion = versionFile.read().strip()


    instance = None

    def __init__(self):
        if not os.path.isdir("data"):
            os.mkdir("data")

        if not State.instance:
            State.instance = State.__State()

    @retry
    def updateMods(self):
        self.instance.updateMods()

    def __getattr__(self, name):
        data = getattr(self.instance, "data")
        if name in data:
            return data[name]

        return getattr(self.instance, name)

    def setState(self, values):
        data = self.data
        for key in values.keys():
            data[key] = values[key]

        ImportExportHelper.exportData(data)
        self.data = data

    def awardWin(self, username, comment):
        roundNumber = self.roundNumber
        roundWonTime = utils.getCreationTime(comment)

        numWins = 0
        rounds = []

        self.setState({
            "roundNumber": roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "roundWonTime": roundWonTime,
        })
