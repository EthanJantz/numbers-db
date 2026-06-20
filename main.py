import argparse
import json
import re

import config
from api import KagiSearch, OEISSearch, OpenRouter, WikiSearch
from song import play_sequence


def select_index(raw, count):
    """Pull a result index out of the model's reply, defensively.

    Prefers a JSON object like {"index": N}; falls back to the first integer
    found in the text. The result is clamped to a valid 0..count-1 index so a
    misbehaving model can never raise an IndexError downstream.
    """
    index = 0
    try:
        index = int(json.loads(raw)["index"])
    except (ValueError, KeyError, TypeError):
        match = re.search(r"\d+", raw)
        if match:
            index = int(match.group())

    return max(0, min(index, count - 1))


def main():
    parser = argparse.ArgumentParser(
        prog="NumbersDB", description="Tells you about a number", epilog="Bottom text"
    )

    parser.add_argument("query")
    # parser.add_argument("-e", "--engine", default="wiki")
    args = parser.parse_args()
    # print(args.query, args.engine)

    wiki = WikiSearch()
    kagi = KagiSearch(config.KAGI_API_KEY)
    oeis = OEISSearch()

    llm = OpenRouter(config.OPENROUTER_API_KEY)

    wiki_results = wiki.query(args.query, 10)

    prompt = f"Provide a brief, concise description of the number {args.query} based on the provided data. Do not reference said data or speak about the data contents in your description. The description should be of the number as if it has a personality and a meaningful history -- if you must you can embellish but it cannot be overemphasized how important it is to not treat the description as a summary of historical data. {wiki_results}"
    response = llm.prompt(prompt)
    num_description_msg = response["choices"][0]["message"]["content"]
    # print(num_description_msg)

    kagi_results = kagi.query(args.query, 10)
    prompt = (
        f"Description of the number:\n{num_description_msg}\n\n"
        f"Search results (a JSON array):\n{kagi_results}\n\n"
        "Return the zero-based index of the single result whose contents best "
        'match the description. Respond with ONLY a JSON object like {"index": 0}.'
    )
    response = llm.prompt(
        prompt,
        system="You are a selector. You output only what is asked, with no "
        "preamble, commentary, or markdown.",
        response_format={"type": "json_object"},
    )
    raw = response["choices"][0]["message"]["content"]
    num_best_result = kagi_results[select_index(raw, len(kagi_results))]
    print(num_best_result)

    oeis_results = oeis.query(args.query)
    sequence = oeis_results["sequence"]
    idx = sequence.index(int(args.query))
    trunc_sequence = sequence[idx - 8 : idx] + sequence[idx : idx + 8]
    song = [x % 12 for x in trunc_sequence]
    play_sequence(song)


if __name__ == "__main__":
    main()
