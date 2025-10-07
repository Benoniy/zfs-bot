#!/bin/bash

sudo systemctl stop zfs-bot.service
git pull
sudo systemctl start zfs-bot.service