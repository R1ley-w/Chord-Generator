#!/usr/bin/env python3
"""Command-line entry point for the Jazz Chord Generator.

Run the automated demo:

    python main.py

or the interactive session:

    python main.py --interactive
"""

import sys

from chord_generator.app import demo_complete_app, interactive_demo


def main() -> None:
    if "--interactive" in sys.argv:
        interactive_demo()
    else:
        demo_complete_app()


if __name__ == "__main__":
    main()
