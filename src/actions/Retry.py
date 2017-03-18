from prawcore import exceptions
from time import sleep
import traceback

from save import Logger

def actionWithRetry(action, *args):
    '''Perform the given action. If an exception is raised, retry every ten seconds
    Return the return value of the action, if any'''

    failCount = 0
    while True:
        try:
            result = action(*args)

            if failCount > 0:
                Logger.log("Action {} succeeded after {} failures".format(action.__name__, failCount))

            return result

        except exceptions.BadRequest:
            # Don't keep trying if we get a bad request - this is likely caused by deleted accounts so we can safely ignore them
            Logger.log("Action {} failed with HTTP status 400. Returning...".format(action.__name__))
            return

        except Exception as e:
            failCount += 1

            if failCount == 1:
                Logger.log("Action {} failed with error message: {}".format(action.__name__, e))
                Logger.log("Stacktrace:\n{}".format("".join(traceback.format_stack())))

            sleep(10)
            continue
