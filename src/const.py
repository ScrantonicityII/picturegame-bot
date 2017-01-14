import re

AUTOMOD = "AutoModerator"
DISALLOWED_NAMES = {AUTOMOD}

TITLE_PATTERN = re.compile("^\[round \d+\]", re.I) # ignore case
CORRECT_PATTERN = re.compile("\+correct")
LOW_FLAIR_PATTERN = re.compile("^Round \d+(, \d+)*")
HIGH_FLAIR_PATTERN = re.compile("^\d+ wins")

UNSOLVED_FLAIR = "UNSOLVED"
OVER_FLAIR = "ROUND OVER"

CONVS_URL = "/api/mod/conversations"
ARCHIVE_URL = CONVS_URL + "/{}/archive"
COMMENT_URL = "/comments/{postId}/_/{commentId}"

PLUSCORRECT_REPLY = '''
Congratulations, that was the correct answer! Please continue the game as soon as possible. 
You have been PM'd the instructions for continuing the game.
\n\n
---
^^I ^^am ^^a ^^bot. ^^If ^^I ^^don't ^^work, ^^please [^^PM ^^my ^^master](http://www.reddit.com/message/compose/?to=Provium) 
^^or [^^message ^^the ^^moderators.](http://www.reddit.com/message/compose?to=%2Fr%2FPictureGame)
'''

WINNER_SUBJECT = "Congratulations, you can post the next round!"
WINNER_PM = '''
    Congratulations on winning the last round! \n
    Your account should now be approved to submit to /r/{subredditName} to submit a new round. \n
    Please share how you got the answer in the comments. \n
    Please remember that your title must start with "[Round {roundNum}]".\n\n

---
>[Join the Discord chat](http://discord.gg/013eeoM1NYuYmJH$) and discuss your round live with the PictureGame community!\n\n

>[Submit a new Round](http://www.reddit.com/r/{subredditName}/submit?title=[Round%20{roundNum}])\n\n

---
^First ^time ^winning? ^See ^the [^hosting ^guide](/r/picturegame/wiki/hosting)
'''

ROUND_OVER_STICKY = '''
#Congratulations to {winnerName} on winning this round!\n\n

The correct answer was:\n\n
[{roundAnswer}](/spoiler)\n\n
[Go to winning comment]({commentLink})
'''

REJECTION_COMMENT = '''
Your submission has been rejected because you have not titled it correctly!\n\n

Please re-post your round with the following title:\n\n
>{correctTitle}
'''
