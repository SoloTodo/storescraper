import json
from datetime import datetime
from decimal import Decimal
import dateutil.parser
import validators

import pytz

from .utils import check_ean13
from .currency import Currency


class Product:
    VALID_CONDITIONS = [
        "https://schema.org/DamagedCondition",
        "https://schema.org/NewCondition",
        "https://schema.org/RefurbishedCondition",
        "https://schema.org/UsedCondition",
        # This is not part of the schema standard
        "https://schema.org/OpenBoxCondition",
    ]

    def __init__(
        self,
        name,
        store,
        category,
        url,
        discovery_url,
        key,
        stock,
        normal_price,
        offer_price,
        currency,
        part_number=None,
        sku=None,
        ean=None,
        description=None,
        cell_plan_name=None,
        cell_monthly_payment=None,
        picture_urls=None,
        timestamp=None,
        condition="https://schema.org/NewCondition",
        positions=None,
        video_urls=None,
        review_count=None,
        review_avg_score=None,
        flixmedia_id=None,
        has_virtual_assistant=None,
        seller=None,
        allow_zero_prices=False,
    ):
        assert isinstance(key, str)
        assert isinstance(stock, int)
        assert len(name) <= 256
        assert len(key) <= 256
        assert len(url) <= 512
        assert len(discovery_url) <= 512
        assert normal_price >= offer_price, (normal_price, offer_price)

        for price in [normal_price, offer_price]:
            price_metadata = price.as_tuple()
            assert price_metadata.exponent >= -2, price
            assert (len(price_metadata.digits) + price_metadata.exponent) <= 10, price

        if cell_plan_name:
            assert len(cell_plan_name) <= 60

        if picture_urls:
            for picture_url in picture_urls:
                assert validators.url(picture_url), picture_url

        if video_urls:
            for video_url in video_urls:
                assert validators.url(video_url), video_url

        if ean:
            assert check_ean13(ean), ean

        if part_number and len(part_number) > 50:
            raise Exception("Invalid part number: {}".format(part_number))

        assert part_number != ""

        if sku and len(sku) > 50:
            raise Exception("Invalid SKU: {}".format(sku))

        if review_count:
            assert isinstance(review_count, int)

        if review_avg_score:
            assert isinstance(review_avg_score, float)

        if flixmedia_id:
            assert isinstance(flixmedia_id, str)

        if has_virtual_assistant:
            assert isinstance(has_virtual_assistant, bool)

        if seller:
            assert len(seller) <= 256

        if (not normal_price or not offer_price) and not allow_zero_prices:
            raise Exception("Price cannot be zero")

        assert condition in Product.VALID_CONDITIONS

        self.name = name
        self.store = store
        self.category = category
        self.url = url
        self.discovery_url = discovery_url
        self.key = key
        self.stock = stock
        self.normal_price = normal_price
        self.offer_price = offer_price
        self.currency = currency
        self.part_number = part_number
        self.sku = sku
        self.ean = ean
        self.description = description
        self.cell_plan_name = cell_plan_name
        self.cell_monthly_payment = cell_monthly_payment
        self.picture_urls = picture_urls
        if not timestamp:
            timestamp = datetime.utcnow()
        if not timestamp.tzinfo:
            timestamp = pytz.utc.localize(timestamp)
        self.condition = condition
        self.positions = positions or []
        self.video_urls = video_urls
        self.review_count = review_count
        self.review_avg_score = review_avg_score
        self.flixmedia_id = flixmedia_id
        self.has_virtual_assistant = has_virtual_assistant
        self.timestamp = timestamp
        self.seller = seller
        self.allow_zero_prices = allow_zero_prices

    def __str__(self):
        lines = list()
        lines.append("{} - {} ({})".format(self.store, self.name, self.category))
        lines.append(self.url)
        lines.append("Discovery URL: {}".format(self.discovery_url))
        lines.append("SKU: {}".format(self.optional_field_as_string("sku")))
        lines.append("EAN: {}".format(self.optional_field_as_string("ean")))
        lines.append(
            "Part number: {}".format(self.optional_field_as_string("part_number"))
        )
        lines.append(
            "Picture URLs: {}".format(self.optional_field_as_string("picture_urls"))
        )
        lines.append(
            "Video URLs: {}".format(self.optional_field_as_string("video_urls"))
        )
        lines.append("Key: {}".format(self.key))
        lines.append("Stock: {}".format(self.stock_as_string()))
        lines.append("Currency: {}".format(self.currency))
        lines.append(
            "Normal price: {}".format(Currency.format(self.normal_price, self.currency))
        )
        lines.append(
            "Offer price: {}".format(Currency.format(self.offer_price, self.currency))
        )
        lines.append("Condition: {}".format(self.condition))
        lines.append(
            "Review count: {}".format(self.optional_field_as_string("review_count"))
        )
        lines.append(
            "Review avg score: {}".format(
                self.optional_field_as_string("review_avg_score")
            )
        )
        lines.append(
            "Flixmedia ID: {}".format(self.optional_field_as_string("flixmedia_id"))
        )
        lines.append(
            "Virtual assistant: {}".format(
                self.optional_field_as_string("has_virtual_assistant")
            )
        )
        lines.append("Seller: {}".format(self.optional_field_as_string("seller")))
        lines.append("Positions: {}".format(self.positions))
        lines.append(
            "Cell plan name: {}".format(self.optional_field_as_string("cell_plan_name"))
        )

        cell_monthly_payment = self.cell_monthly_payment

        if cell_monthly_payment is None:
            cell_monthly_payment_string = "N/A"
        else:
            cell_monthly_payment_string = Currency.format(
                cell_monthly_payment, self.currency
            )

        lines.append("Cell monthly payment: {}".format(cell_monthly_payment_string))
        lines.append("Timestamp: {}".format(self.timestamp.isoformat()))

        lines.append(
            "Description: {}".format(self.optional_field_as_string("description")[:30])
        )

        return "\n".join(lines)

    def __repr__(self):
        return "{} - {}".format(self.store, self.name)

    def serialize(self):
        serialized_cell_monthly_payment = (
            str(self.cell_monthly_payment)
            if self.cell_monthly_payment is not None
            else None
        )

        return {
            "name": self.name,
            "store": self.store,
            "category": self.category,
            "url": self.url,
            "discovery_url": self.discovery_url,
            "key": self.key,
            "stock": self.stock,
            "normal_price": str(self.normal_price),
            "offer_price": str(self.offer_price),
            "currency": self.currency,
            "part_number": self.part_number,
            "sku": self.sku,
            "ean": self.ean,
            "description": self.description,
            "cell_plan_name": self.cell_plan_name,
            "cell_monthly_payment": serialized_cell_monthly_payment,
            "picture_urls": self.picture_urls,
            "video_urls": self.video_urls,
            "timestamp": self.timestamp.isoformat(),
            "condition": self.condition,
            "positions": self.positions,
            "review_count": self.review_count,
            "review_avg_score": self.review_avg_score,
            "flixmedia_id": self.flixmedia_id,
            "has_virtual_assistant": self.has_virtual_assistant,
            "seller": self.seller,
            "allow_zero_prices": self.allow_zero_prices,
        }

    @classmethod
    def deserialize(cls, serialized_data):
        serialized_data["normal_price"] = Decimal(serialized_data["normal_price"])
        serialized_data["offer_price"] = Decimal(serialized_data["offer_price"])

        cell_monthly_payment = serialized_data["cell_monthly_payment"]
        if cell_monthly_payment:
            cell_monthly_payment = Decimal(cell_monthly_payment)

        serialized_data["cell_monthly_payment"] = cell_monthly_payment

        serialized_data["timestamp"] = dateutil.parser.parse(
            serialized_data["timestamp"]
        )
        return cls(**serialized_data)

    def is_available(self):
        return self.stock != 0

    ##########################################################################
    # Utility methods
    ##########################################################################

    def stock_as_string(self):
        if self.stock == -1:
            return "Available but unknown"
        elif self.stock == 0:
            return "Unavailable"
        else:
            return str(self.stock)

    def optional_field_as_string(self, field):
        field_value = getattr(self, field)
        if field_value is not None:
            return field_value
        else:
            return "N/A"

    def picture_urls_as_json(self):
        if self.picture_urls is None:
            return None
        return json.dumps(self.picture_urls)

    def picture_urls_count(self):
        if self.picture_urls is None:
            return None
        return len(self.picture_urls)

    def video_urls_as_json(self):
        if self.video_urls is None:
            return None
        return json.dumps(self.video_urls)

    def video_urls_count(self):
        if self.video_urls is None:
            return None
        return len(self.video_urls)
