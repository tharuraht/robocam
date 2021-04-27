#!/bin/bash
#Adapted from https://gist.github.com/mattkasun/9a0e90d9d31b2c935d3f6d6e71dbece9
#Attempts to ping host machine, restarts wireguard after number of tries
tries=0
while [[ $tries -lt 3 ]]
do
        if /bin/ping -c 1 -i 1 10.200.200.1 #1s timeout
        then
              echo "wg working"
                # logger -n winterfell -i -t "wg-watchdog" -p user.notice "wireguard working"
                exit 0
        fi
##      echo "wg fail"
        tries=$((tries+1))
done
echo "restarting wg"
sudo systemctl restart wg-quick@wg0-client
# logger -n winterfell -i -t "wg-watchdog" -p user.notice "wireguard restarted"

#crontab entry
#*/15 * * * * /home/mkasun/bin/wg-watchdog.sh
