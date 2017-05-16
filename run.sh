#!/bin/bash
if [ -f data/bot.log ]; then
    mv data/bot.log data/bot.log.1
fi

./run.py
