#!/bin/bash
pylint3 ./**/*.py -d broad-except -d global-statement > pylint.txt
