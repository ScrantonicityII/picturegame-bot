#!/bin/bash
if [ ! -d data ]; then
    mkdir data
fi

if [ -f data/bot.log ]; then
    mv data/bot.log data/bot.log.1
fi

./main.py
