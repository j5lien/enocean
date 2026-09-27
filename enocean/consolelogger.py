import logging
import logging.handlers


def init_logging(level: int = logging.DEBUG, log_to_file: bool = False, logsize: int = 1024, logcount: int = 5) -> None:
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
