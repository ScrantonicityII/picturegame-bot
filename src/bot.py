#!/usr/bin/python3

import praw
import save.ImportExportHelper as ImportExportHelper

from const import *


def main():
    print("PictureGame Bot by Provium")
    reddit = praw.Reddit(SCRIPT_NAME)
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    
    bot_data = ImportExportHelper.import_data(subreddit)


if __name__ == "__main__":
    main()
