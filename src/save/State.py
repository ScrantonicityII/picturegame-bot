import configparser
import json
import logging
import os
import praw

from ..const import CONFIG_FILENAME

from ..actions.Retry import retry
from ..reddit import Wiki, utils

from . import ImportExportHelper


class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    class __State:
        def __init__(self, args):
            self.setupConfig(args.env)
            self.setupLogging(args.logConfig)

            logging.info("Initialising State")

            self.reddit = praw.Reddit(self.config["scriptName"])
            self.subreddit = self.reddit.subreddit(self.config["subredditName"])
            self.updateMods()

            self.data = ImportExportHelper.importData(self)
            self.seenComments = set()
            self.seenPosts = set()
            self.commentedRoundIds = {} # keys = round ids, values = comment objects
            self.apiSessionToken = ""

        def updateMods(self):
            self.mods = set(map(lambda mod: mod.name, self.subreddit.moderator()))

        def setupConfig(self, sectionName):
            config = configparser.ConfigParser(converters = {"lower": lambda x: x.lower()})
            config.read(CONFIG_FILENAME)
            self.config = config[sectionName]

        def setupLogging(self, logConfigFile):
            configFile = logConfigFile if logConfigFile is not None else self.config["logConfig"]
            with open(configFile) as logConfig:
                logging.config.dictConfig(json.loads(logConfig.read()))

            logging.info("Successfully configured logging using config file %s", configFile)


    instance = None

    def __init__(self, args):
        if not os.path.isdir("data"):
            os.mkdir("data")

        if not State.instance:
            State.instance = State.__State(args)

    @retry
    def updateMods(self):
        self.instance.updateMods()

    def __getattr__(self, name):
        if name == "leaderboard":
            return Wiki.scrapeLeaderboard(self.subreddit)

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
        leaderboard = self.leaderboard
        roundNumber = self.roundNumber
        roundWonTime = utils.getCreationTime(comment)

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
            "rounds": rounds,
        }

        self.setState({
            "roundNumber": roundNumber + 1,
            "currentHost": username,
            "unsolved": False,
            "roundWonTime": roundWonTime,
        })

        ImportExportHelper.exportLeaderboard(self.subreddit, leaderboard)
