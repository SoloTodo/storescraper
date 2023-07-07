#!/bin/sh
env/bin/pipdeptree -f --warn silence | grep -E '^[a-zA-Z0-9\-]+'
