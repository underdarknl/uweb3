import logging

DEBUG_FORMAT = (
    "%(levelname)s - %(page_maker)s - %(method)s - "
    + "%(route)s - (%(filename)s:%(lineno)d) \n%(message)s\n"
    + "GET data: %(get)s\n"
    + "POST:data: %(post)s"
)

RED_COLOR = "\x1b[31;20m"
RESET_COLOR = "\x1b[0m"


def create_file_handler(path: str) -> logging.FileHandler:
    """Setup a Filehandler with a default configuration.
    
    Returns:
        logging.FileHandler: The default FileHandler.
    """
    return logging.FileHandler(
        path,
        encoding="utf-8",
    )


def setup_debug_logger(path: str) -> logging.FileHandler:
    """Setup formatting and loglevel for the debug file logger

    Args:
        path (str): Full path to the logfile including extension.
    Returns:
        logging.FileHandler: The filehandler for this logger
    """
    fh = create_file_handler(path)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(DEBUG_FORMAT)
    fh.setFormatter(formatter)
    return fh


def setup_debug_stream_logger() -> logging.StreamHandler:
    """Setup formatting for the debug stream logger

    Returns:
        logging.StreamHandler: The streamhandler for this logger
    """
    debug_stream = logging.StreamHandler()
    debug_stream.setLevel(logging.DEBUG)

    debug_format = logging.Formatter(f"{RED_COLOR}{DEBUG_FORMAT}{RESET_COLOR}")
    debug_stream.setFormatter(debug_format)
    return debug_stream


def setup_error_logger(path: str) -> logging.FileHandler:
    """Setup formatting and loglevel for the error logger
    Args:
        path (str): Full path to the logfile including extension.
    Returns:
        logging.FileHandler: The filehandler for this logger
    """

    fh = create_file_handler(path)
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(page_maker)s - %(method)s - %(route)s - %(message)s"
    )
    fh.setFormatter(formatter)
    return fh
