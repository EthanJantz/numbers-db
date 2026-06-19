import argparse

import anthropic

import config
from search import KagiSearch, WikiSearch

client = anthropic.Anthropic()


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

    results = search.query(args.query, 10)
    # pprint.pprint(results)

    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Provide a brief, concise description of the number {args.query} based on the provided data.
                Do not reference said data or speak about the data contents in your description.
                The description should be of the number as if it has a personality and a meaningful history -- if you must you can embellish
                but it cannot be overemphasized how important it is to not treat the description as a summary of historical data.
                {results}""",
            }
        ],
    )

    print(message.content[0].text)  # ty: ignore[unresolved-attribute]


if __name__ == "__main__":
    main()
