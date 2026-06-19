import argparse

import config
from search import KagiSearch, WikiSearch


def main():
    parser = argparse.ArgumentParser(
        prog="NumbersDB", description="Tells you about a number", epilog="Bottom text"
    )

    parser.add_argument("query")
    parser.add_argument("-e", "--engine", default="wiki")
    args = parser.parse_args()
    print(args.query, args.engine)

    if args.engine == "web":
        search = KagiSearch(config.KAGI_API_KEY)
    else:
        search = WikiSearch()

    results = search.query(args.query, 10)

    print(results)


if __name__ == "__main__":
    main()
