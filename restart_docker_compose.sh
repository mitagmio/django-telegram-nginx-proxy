#!/bin/bash
docker compose down
sleep 2
screen -X -S log quit
docker compose up -d