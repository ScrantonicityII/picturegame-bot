# pylint: disable=line-too-long

import re

AUTOMOD = "automoderator"
DISALLOWED_NAMES = {AUTOMOD}

TITLE_PATTERN = re.compile(r"^\[round \d+\]", re.I) # ignore case
TITLE_CORRECTION_PATTERN = re.compile(
    r"^\s*[\(\{\[\<]?\s*(round)?\s*\d*\s*[\)\}\]\>]?\s*:?\s*", re.I)
CORRECT_PATTERN = re.compile(r"\+correct")
HIGH_FLAIR_PATTERN = re.compile(r"^(\d+ wins)|$")

def LOW_FLAIR_PATTERN(numRounds):
    pattern = r"^(Round \d+(, \d+){0,%d})|$" % (numRounds - 1)
    return re.compile(pattern)

UNSOLVED_FLAIR = "UNSOLVED"
OVER_FLAIR = "ROUND OVER"
ABANDONED_FLAIRS = {OVER_FLAIR, "ABANDONED", "TERMINATED"}

CONVS_URL = "/api/mod/conversations"
ARCHIVE_URL = CONVS_URL + "/{}/archive"
COMMENT_URL = "/comments/{postId}/_/{commentId}"
PG_API_URL = "http://pg-api.w5qpeynevs.us-west-2.elasticbeanstalk.com"

CONFIG_FILENAME = "bot.ini"

COMMENT_FOOTER = '''

---
^^I ^^am ^^a ^^bot. ^^If ^^I ^^don't ^^work, ^^please [^^PM ^^my ^^master](http://www.reddit.com/message/compose/?to=Provium) 
^^or [^^message ^^the ^^moderators.](http://www.reddit.com/message/compose?to=%2Fr%2FPictureGame)    
[^^Learn ^^more](/r/PictureGame_Bot)'''

PLUSCORRECT_REPLY = '''Congratulations, that was the correct answer! Please continue the game as soon as possible.
You have been PM'd the instructions for continuing the game.''' + COMMENT_FOOTER

WINNER_SUBJECT = "Congratulations, you can post the next round!"
WINNER_PM = '''
    Congratulations on winning the last round!

    Your account should now be approved to submit to /r/{subredditName} to submit a new round.

    Please share how you got the answer in the comments.

    Please remember that your title must start with "[Round {roundNum}]".

---
>[Join the Discord chat](https://discord.gg/D2t9fN2) and discuss your round live with the PictureGame community!

>[Submit a new Round](http://www.reddit.com/r/{subredditName}/submit?title=[Round%20{roundNum}])

---
^First ^time ^winning? ^See ^the [^hosting ^guide](/r/picturegame/wiki/hosting)''' + COMMENT_FOOTER

ROUND_OVER_STICKY = '''#Congratulations to {winnerName} on winning this round!

The correct answer was:

{spoileredAnswer}

[Go to winning comment]({commentLink})''' + COMMENT_FOOTER

REJECTION_COMMENT = '''Your submission has been rejected because you have not titled it correctly!

Please re-post your round with the following title:

[{correctTitle}](http://www.reddit.com/r/{subredditName}/submit?title={correctTitle})''' + COMMENT_FOOTER

NEW_ROUND_COMMENT = '''#*Chat*:

Join the official [{subredditName} Discord](https://discord.gg/D2t9fN2) chat to discuss this and future rounds!

Mobile apps also available: [Apple](https://itunes.apple.com/us/app/discord-chat-for-gamers/id985746746?mt=8), [Android](https://play.google.com/store/apps/details?id=com.discord&hl=en)

#*{hostName}*:

Thank you for posting a new round. Please remember leaving a round without +correcting the winner is a **punishable  offence**.

If a user guesses correctly simply respond with *+correct*, the bot will do the rest of the work for you (unless the [bot is down](/r/{subredditName}/wiki/hosting#wiki_bot_not_responding.3F))

**Confused or new?** See the [hosting guide](/r/{subredditName}/wiki/hosting) for the answer to all your problems.
#*Other users*:

Please remember *if you answer correctly you will need to host the next round.* **New?** See our [guide](/r/{subredditName}/wiki/beginners)''' + COMMENT_FOOTER

DUPLICATE_ROUND_REPLY = '''It looks like you've posted something new while there is already a round ongoing [here]({roundUrl}).

If you want this post to replace the earlier posting, please **delete the earlier posting**, and I will start watching this thread instead. Otherwise 
this thread will be removed when the round is over.''' + COMMENT_FOOTER

LEADERBOARD_HEADER = '''# Leaderboard

Rank | Username | Rounds won | Total |
|:--:|:--:|:--|:--:|:--:|
'''
