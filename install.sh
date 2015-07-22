#!/usr/bin/env bash

# Set up OS, assume log in as ubuntu
sudo apt-get update
sudo apt-get -y install python-pip python-virtualenv python3-dev libgpgme11-dev unzip
sudo apt-get -y install git git-review

wget https://codeload.github.com/eResearchSA/nectar-doco-bot/zip/master -qO bot.zip
unzip -q bot.zip

mkdir nectar_doco_bot_env
virtualenv -p python3 nectar_doco_bot_env
source ~/nectar_doco_bot_env/bin/activate
pip install -r ~/nectar-doco-bot-master/requirements.txt
deactivate

# config gpg before run the script
git clone https://github.com/NeCTAR-RC/nectarcloud-tier0doco.git

# Once everything has been settled: most important - gpg
# run the script by assuming repo is cloned to ~/nectarcloud-tier0doco
# ~/nectar-doco-bot-master/script/fdbroker.py &