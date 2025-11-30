#!/usr/bin/env sh

. ./.env/bin/activate
python3 ./src/main.py &
cd src/medassist-fe/build && python -m http.server 8080
