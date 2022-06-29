import logging

DEBUG_FORMAT = (
    "%(levelname)s - %(page_maker)s - %(method)s - "
    + "%(route)s - (%(filename)s:%(lineno)d) \n%(message)s\n"
    + "GET data: %(get)s\n"
    + "POST:data: %(post)s"
)


def setup_debug_logger(path: str):
    fh = logging.FileHandler(
        path,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(DEBUG_FORMAT)
    fh.setFormatter(formatter)
    return fh


def setup_debug_stream_logger():
    debug_stream = logging.StreamHandler()
    debug_stream.setLevel(logging.DEBUG)

    debug_format = logging.Formatter(f"\x1b[31;20m{DEBUG_FORMAT}\x1b[0m")
    debug_stream.setFormatter(debug_format)
    return debug_stream


def setup_error_logger(path: str):
    fh = logging.FileHandler(
        path,
        encoding="utf-8",
    )
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(page_maker)s - %(method)s - %(route)s - %(message)s"
    )
    fh.setFormatter(formatter)
    return fh
