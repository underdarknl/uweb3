#!/usr/bin/python3
"""Starts a simple application development server.
Just execute `./serve.py` or `python3 serve.py`
"""

# Application
from test import uweb3tests


def main():
    app = uweb3tests.main()
    app.serve()


if __name__ == "__main__":
    main()
