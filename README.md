# picturegame-bot
A complete rewrite of the Reddit bot behind /r/PictureGame.

## Features
The new bot has all the same features of the old one, with some additions:
* Automatically respond to new rounds with a standard message
* Maintain a correctly numbered leaderboard on the subreddit wiki
* Check each round is titled with the correct format `[Round xxx]` and that `xxx` is the correct number
 * Remove incorrectly titled rounds and give the OP information about where they went wrong

## Dependencies
* `PRAW` version 4 or 5. 5 is recommended for performance reasons.

## Installation
* Install `praw`
 * `pip install praw`
* Setup your `praw.ini` file as explained in [this guide](https://praw.readthedocs.io/en/v4.0.0/getting_started/configuration/prawini.html)
 * As per the `Defining Additional Sites` section, the last few lines of your `praw.ini` should be as follows:
```
[<name of your choice>]
client_id=<client id supplied by reddit>
client_secret=<client secret supplied by reddit>
password=<password of bot account>
username=<username of bot account>
user_agent=PictureGame Bot 2.0
```
* Clone the bot
 * `git clone https://github.com/hswhite33/picturegame-bot.git`

## Configuration
Configuration must be stored in `bot.ini` in the same directory as `main.py`. See `sample.ini` for details.

In addition, config for logging must be specified in JSON format according to Python's specification [here](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig)
Sample configs for both dev and prod are provided in the repo.

## Usage
```
cd picturegame-bot
./main.py --env <SectionName>
```

This will run the bot using the configuration under the `<SectionName>` section in `bot.ini`.
