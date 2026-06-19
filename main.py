import argparse

import config
from api import KagiSearch, OpenRouter, WikiSearch


def main():
    parser = argparse.ArgumentParser(
        prog="NumbersDB", description="Tells you about a number", epilog="Bottom text"
    )

    parser.add_argument("query")
    parser.add_argument("-e", "--engine", default="wiki")
    args = parser.parse_args()
    # print(args.query, args.engine)

    if args.engine == "web":
        search = KagiSearch(config.KAGI_API_KEY)
    else:
        search = WikiSearch()

    llm = OpenRouter(config.OPENROUTER_API_KEY)

    results = search.query(args.query, 10)
    # pprint.pprint(results)

    response = llm.query(results, args.query)
    msg = response["choices"][0]["message"]["content"]
    # pprint.pprint(response)
    print(msg)


if __name__ == "__main__":
    main()
