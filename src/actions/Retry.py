from time import sleep
from prawcore import exceptions

from save import Logger

def actionWithRetry(action, *args):
    '''Perform the given action. If an exception is raised, retry every ten seconds
    Return the return value of the action, if any'''

    while True:
        try:
            result = action(*args)
            return result

        except exceptions.BadRequest:
            # Don't keep trying if we get a bad request - this is likely caused by deleted accounts so we can safely ignore them
            Logger.log("Action {} failed with HTTP status 400. Returning...".format(action.__name__))
            return

        except Exception as e:
            Logger.log("Action {} failed with error message: {}, retrying in 10 seconds...".format(action.__name__, e))
            sleep(10)
            continue
