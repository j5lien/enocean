"""Logging setup for applications and examples using the library."""

import datetime
import json
import logging
import logging.handlers

# Attributes every LogRecord has; anything else was passed through `extra=` and is emitted as a field
_RECORD_ATTRIBUTES = set(vars(logging.makeLogRecord({}))) | {'message', 'asctime', 'taskName'}


class JsonFormatter(logging.Formatter):
    """Formats records as one JSON object per line, including fields passed with `extra=`."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a record as a JSON object: time, level, logger, message, extra fields, exception."""
        entry: dict[str, object] = {
            'time': datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        entry.update({key: value for key, value in vars(record).items() if key not in _RECORD_ATTRIBUTES})
        if record.exc_info:
            entry['exception'] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def init_logging(
    level: int = logging.DEBUG,
    log_to_file: bool = False,
    logsize: int = 1024,
    logcount: int = 5,
    json_format: bool = False,
) -> None:
    """Send the library's logs to stderr, and optionally to a rotating enocean.log file.

    Args:
        level: Minimum level of the records emitted.
        log_to_file: Also write to enocean.log in the working directory.
        logsize: Maximum size of enocean.log, in kB, before it is rotated.
        logcount: Number of rotated files kept.
        json_format: Emit one JSON object per record, carrying structured fields such as packet_type, rorg, sender.
    """
    formatter: logging.Formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger('enocean')
    logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler('enocean.log', 'a', logsize * 1000, logcount)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
