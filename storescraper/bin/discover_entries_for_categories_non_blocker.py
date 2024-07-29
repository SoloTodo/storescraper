import argparse
import json
import logging
import sys

sys.path.append("../..")

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.basicConfig(level=logging.WARNING, stream=sys.stdout)

    parser = argparse.ArgumentParser(
        description="Discovers the URLs of the given store and (optional) " "categories"
    )
    parser.add_argument("store", type=str, help="The name of the store to be parsed")
    parser.add_argument(
        "--categories", type=str, nargs="*", help="Specific categories to be parsed"
    )
    parser.add_argument(
        "--extra_args",
        type=json.loads,
        nargs="?",
        default={},
        help="Optional arguments to pass to the parser "
        "(usually username/password) for private sites)",
    )

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)

    store.discover_entries_for_categories_non_blocker(
        categories=args.categories, extra_args=args.extra_args
    )


if __name__ == "__main__":
    main()
