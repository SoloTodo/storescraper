#!/usr/bin/env bash
celery multi start storescraper -Q:storescraper storescraper -c:storescraper 30 -E -l info --config=celeryconfig
