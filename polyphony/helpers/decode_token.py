import base64
import logging

from polyphony.settings import DEBUG

log = logging.getLogger(__name__)


def decode_token(token: str):
    token = token.split(".")
    if DEBUG is TRUE:
        log.info(string(base64.b64decode(token[0])))
    return int(base64.b64decode(token[0]))
