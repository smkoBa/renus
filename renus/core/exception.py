import traceback
import json

from renus.core.status import Status
from renus.core.config import Config
from renus.core.log import Log


def abort(msg, status_code: Status = Status.HTTP_400_BAD_REQUEST):
    raise RuntimeError(msg, status_code)


def abort_if(condition: bool, msg, status_code: Status = Status.HTTP_400_BAD_REQUEST):
    if condition:
        raise RuntimeError(msg, status_code)

def abort_unless(condition: bool, msg, status_code: Status = Status.HTTP_400_BAD_REQUEST):
    if not condition:
        raise RuntimeError(msg, status_code)


def debug_response(exc: Exception):
    if len(exc.args) > 1:
        return exc.args[0], exc.args[1]

    status_code = Status.HTTP_500_INTERNAL_SERVER_ERROR
    traceback_obj = traceback.TracebackException.from_exception(
        exc, capture_locals=True
    )
    error = f"{traceback_obj.exc_type.__name__}: {str(traceback_obj)}"
    stacks = traceback_obj.stack.format()
    stack_list = []
    for stack in stacks:
        stack_list.append(stack.split('\n'))

    res = {
        'msg': error,
        'file': traceback.format_tb(exc.__traceback__),
        'stack': stack_list,
    }
    Log().error(json.dumps(
            res,
            ensure_ascii=False,
            allow_nan=True,
            indent=4,
            separators=(",", ":"),
        ))
    if not Config('app').get('debug', False):
        return {
                'msg': 'Internal Server Error',
            },status_code

    return res,status_code
