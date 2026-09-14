import json
import logging


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("support_assistant")
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_event(event: str, **fields: object) -> None:
    logging.getLogger("support_assistant").info(json.dumps({"event": event, **fields}, default=str))


def log_exception(event: str, **fields: object) -> None:
    logging.getLogger("support_assistant").exception(json.dumps({"event": event, **fields}, default=str))