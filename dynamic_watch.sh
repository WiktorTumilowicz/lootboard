#!/bin/bash

watchmedo shell-command \
    --patterns="lootboard.py" \
    --command='clear && python3 lootboard.py' \
    --wait
