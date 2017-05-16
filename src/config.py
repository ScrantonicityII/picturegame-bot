import getpass
import json

from .const import *

FileName = "data/config.json"

'''
Global config object

Access values by using getKey and setKey, don't access directly from here

Required props: "value", "prompt", "index" (index to have a fixed order for prompting)
Optional props: "default", "caseInsensitive", "allowedValues", "promptFunc" (e.g. getpass.getpass for passwords)
'''
config = {
    "scriptName": {"index": 0, "value": None, "prompt": "Enter script name (the same as in praw.ini)"},
    "botName": {"index": 1, "value": None, "prompt": "Enter the reddit username of the bot", "caseInsensitive": True},
    "subredditName": {"index": 2, "value": None, "prompt": "Enter the name of the subreddit"},
    "ownerName": {"index": 3, "value": None, "prompt": "Enter your reddit username"},
    # "username": {"index": 4, "value": None, "prompt": "PG-API Username"},
    # "password": {"index": 5, "value": None, "prompt": "PG-API Password", "promptFunc": getpass.getpass},
    # "pgApiUrl": {"index": 6, "value": None, "prompt": "PG-API URL", "default": PG_API_URL},
    "printLogs": {"index": 7, "value": None, "prompt": "Print logs to stdout", "default": "n", "allowedValues": ['y', 'n']},
    "logLevel": {"index": 8, "value": None, "prompt": "Log level", "default": "w", "allowedValues": ["err", "warn", "info", "debug"], "firstChar": True, "caseInsensitive": True},
}


def getKey(keyName):
    return config[keyName]["value"]


def setKey(keyName, value):
    if config[keyName].get("caseInsensitive"):
        value = value.lower()

    config[keyName]["value"] = value


def promptKey(keyName, promptFunc = input):
    default = config[keyName].get("default", None)

    prompt = config[keyName]["prompt"]
    if default is not None:
        prompt += " (default: {})".format(default)

    if "allowedValues" in config[keyName]:
        prompt += " ({})".format("/".join(
            [transformValue(v, config[keyName].get("firstChar")) for v in config[keyName]["allowedValues"]]))

    while True:
        value = promptFunc(prompt + ": ")
        if config[keyName].get("firstChar") and len(value) > 0:
            value = value[0]

        if config[keyName].get("caseInsensitive"):
            value = value.lower()

        valid = True
        if "allowedValues" in config[keyName]:
            allowedValues = config[keyName]["allowedValues"]
            if config[keyName].get("firstChar"):
                found = next((x for x in allowedValues if x[0] == value.lower()), None)
                if found is None:
                    valid = False
            elif value not in allowedValues:
                valid = False

        if value == "":
            if default is None:
                valid = False
            else:
                valid = True

        if valid:
            break

    if value == "" and default is not None:
        value = default

    setKey(keyName, value)


def transformValue(value, firstLetter):
    if firstLetter:
        return "[{}]{}".format(value[0], value[1:])
    else:
        return value


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
