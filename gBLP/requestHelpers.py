# colorscheme cobalt2 dark
#
# ---------------------------- gBLP LICENCE ---------------------------------
# Licensed under the GNU General Public License, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# ---------------------------------------------------------------------------
from loguru import logger
import datetime as dt
from rich.console import Console; console = Console()
from google.protobuf.timestamp_pb2 import Timestamp as protoTimestamp


def bool_evaluator(protomap: dict) -> dict:
    """ If the values in the map look boolean, then they will be turned
    into a boolean. """
    if not protomap:
        return dict()
    newdict = dict()
    print(type(protomap))
    for k, v in protomap.items():
        if type(v) != str:
            logger.warning(f"Value {v} is not a string.")
        if v.lower() in ["true", "yes", "1"]:
            newdict[k] = True
        elif v.lower() in ["false", "no", "0"]:
            newdict[k] = False
        else:
            newdict[k] = v
    return newdict


def add_dates_to_request_if_missing(request, daysback = 5):
    """ if a request does not have start and end times, stick them in. """
    if not request.HasField("start"):
        start = protoTimestamp()
        start.FromDatetime(dt.datetime.now() - dt.timedelta(days=5))
        request.start.CopyFrom(start)
    if not request.HasField("end"):
        end = protoTimestamp()
        end.FromDatetime(dt.datetime.now())
        request.end.CopyFrom(end)
    return request


def add_overrides_to_bbgrequest(bbgRequest, overrides):
    """ Add overrides to a request. """
    if overrides:
        parsed_ovr = bool_evaluator(overrides)
        overridesElement = bbgRequest.getElement("overrides")
        for k, v in parsed_ovr.items():
            overrideElement = overridesElement.appendElement()
            overrideElement.setElement("fieldId", k)
            overrideElement.setElement("value", v)
    return bbgRequest
