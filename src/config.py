import getpass
import json

FileName = "data/config.json"

'''
Global config object

Access values by using getKey and setKey, don't access directly from here

Required props: "value", "prompt", "index" (index to have a fixed order for prompting)
Optional props: "default", "caseInsensitive", "promptFunc" (e.g. getpass.getpass for passwords)
'''
config = {
    "scriptName": {"index": 0, "value": None, "prompt": "Enter script name (the same as in praw.ini)"},
    "botName": {"index": 1, "value": None, "prompt": "Enter the reddit username of the bot", "caseInsensitive": True},
    "subredditName": {"index": 2, "value": None, "prompt": "Enter the name of the subreddit", "caseInsensitive": True},
    "ownerName": {"index": 3, "value": None, "prompt": "Enter your reddit username"},
    # "username": {"index": 4, "value": None, "prompt": "PG-API Username"},
    # "password": {"index": 5, "value": None, "prompt": "PG-API Password", "promptFunc": getpass.getpass},
}


def getKey(keyName):
    return config[keyName]["value"]


def setKey(keyName, value):
    if config[keyName].get("caseInsensitive"):
        value = value.lower()

    config[keyName]["value"] = value


def promptKey(keyName, promptFunc = input):
    value = "" if "default" not in config[keyName] else config[keyName]["default"]

    prompt = config[keyName]["prompt"]
    if "default" in config[keyName]:
        prompt += " (default: {})".format(config[keyName]["default"])

    while True:
        value = promptFunc(prompt + ": ")
        if value != "":
            break

    setKey(keyName, value)


def loadConfig():
    configData = {}

    with open(FileName) as configFile:
        configData = json.loads(configFile.read())

    for key in configData:
        setKey(key, configData[key])

    generateConfig()


def generateConfig():
    for key in sorted(config, key = lambda x: config[x]["index"]):
        configItem = config[key]
        if configItem["value"] is None:
            if "promptFunc" in configItem:
                promptKey(key, configItem["promptFunc"])
            else:
                promptKey(key)

    dumpConfig()


def dumpConfig():
    configJson = {}
    for key in config:
        configJson[key] = config[key]["value"]

    with open(FileName, 'w') as configFile:
        configFile.write(json.dumps(configJson))