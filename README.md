nectar-doco-bot is an agent for  publishing NeCTAR documents managed in GitHub into Freshdesk. These documents will appear in Freshdesk as articles. More detail on documents see [nectarcloud-tier0doco](https://github.com/NeCTAR-RC/nectarcloud-tier0doco).

## Install the bot

```shell
# log in as ubuntu
wget https://raw.githubusercontent.com/eResearchSA/nectar-doco-bot/master/install.sh
source install.sh
```

This script will:

* update OS,
* install necessary packages,
* set up Python3 virtual environment.

## Run the bot

* set up git account for the bot,
* set up gpg key for the bot,
* activate environment: `source nectar_doco_bot_env/bin/activate`,
* run: `~/nectar-doco-bot-master/script/fdbroker.py -h` first to find out arguments,

    ```shell
    usage: fdbroker.py [-h] [--repopath REPOPATH] [-c CONFNAME] [-ap ARTICLEPATH]
                       [-l {DEBUG,INFO,WARNING,ERROR}]

    Start a Freshdesk bot.

    optional arguments:
      -h, --help            show this help message and exit
      --repopath REPOPATH   Path to Tier0 Doco repository clone (default:
                            /home/ubuntu/nectarcloud-tier0doco)
      -c CONFNAME, --confname CONFNAME
                            Base name of configuration file. Script will look for
                            CONFIGNAME.yaml.asc under script/configs of REPOPATH
                            (default: fdbot)
      -ap ARTICLEPATH, --articlepath ARTICLEPATH
                            articles path relative to repopath (default: articles)
      -l {DEBUG,INFO,WARNING,ERROR}, --loglevel {DEBUG,INFO,WARNING,ERROR}
                            Log level (default: INFO)
    ```

* run `~/nectar-doco-bot-master/script/fdbroker.py` with right arguments starting the bot!

After the bot has been successfully started, it generates a log file: fdbroker.log in the directory it runs. It also prints out the result it runs git commands in the terminal.

## Related link
* [Documents](https://github.com/NeCTAR-RC/nectarcloud-tier0doco)
* [Procedure](https://github.com/NeCTAR-RC/nectarcloud-tier0doco/blob/master/README.md)
