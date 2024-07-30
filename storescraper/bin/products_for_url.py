import argparse
import json
import sys

import logging

sys.path.append("../..")

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        filename="products_for_url.log",
        filemode="w",
    )
    parser = argparse.ArgumentParser(
        description="Retrieves the products of the given store / url"
    )

    parser.add_argument("store", type=str, help="The name of the store to be parsed")

    parser.add_argument("url", type=str, help="Discovery URL of the products")
    parser.add_argument(
        "--category", type=str, nargs="?", help="The product category of the URL"
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
    category = args.category or "Unknown"

    entries = {args.url: {"category": category, "positions": []}}

    products = store.products_for_urls(
        entries, extra_args=args.extra_args, use_async=False
    )

    if products:
        for product in products["products"]:
            print(product, "\n")
    else:
        print("No products found")


if __name__ == "__main__":
    main()
