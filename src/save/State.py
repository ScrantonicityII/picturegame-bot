from . import ImportExportHelper
import praw
from const import *

class State:
    '''Singleton State object - initialised once at the start of the program.
    Subsequent calls to State() return the same instance.'''

    instance = None
    reddit = None
    subreddit = None

    def __init__(self):
        if not State.instance:
            self.reddit = praw.Reddit(SCRIPT_NAME)
            self.subreddit = self.reddit.subreddit(SUBREDDIT_NAME)
            self.instance = ImportExportHelper.import_data(self)

    def __getattr__(self, name):
        if name == "reddit":
            return self.reddit
        if name == "subreddit":
            return self.subreddit
        return self.instance[name]

    def setState(self, attr, value):
        State.instance[attr] = value;
        ImportExportHelper.export_data(State.instance)
