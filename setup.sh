#!/bin/sh

set -e

curl -fs -o master.zip https://codeload.github.com/fedordikarev/skypemanage/zip/master
unzip master.zip
cd skypemanage
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage_members.py -h
