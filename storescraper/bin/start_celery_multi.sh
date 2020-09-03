#!/usr/bin/env bash
celery multi start storescraper -Q:storescraper storescraper -c:storescraper 30 --logfile=./%n.log --pidfile=./%n.pid -E -l info --config=celeryconfig
