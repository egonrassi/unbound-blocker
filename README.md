# unbound-blocker
Unbound Resolver middle layer to block domains from a public list without the need of a restart of the service.
This middle layer utilizes the unbound control to add and remove unwanted domains. Unwanted domains are defined to return NXdomain.

Example:
```
unbound-blocker.py --input URL1 --input URL2 --ignore ".+\.is"
```

Copy the script to /usr/local/bin
Run it according to a timer with systemd
Define the input arguments in the environmental file found in either /etc/sysconfig or /etc/default
The environmental file should hold the following
```
ARGS="--input URL1 --commit"
```

```
pip3 install -r requirements.txt

curl -o /usr/local/bin/unbound-blocker.py https://raw.githubusercontent.com/egonrassi/unbound-blocker/main/unbound-blocker.py 
chmod +x /usr/local/bin/unbound-blocker.py


cat <<EOF > /etc/systemd/system/unbound-blocker.service
[Unit]
Description=unbound-blocker

[Service]
EnvironmentFile=-/etc/sysconfig/unbound-blocker
EnvironmentFile=-/etc/default/unbound-blocker
ExecStart=/usr/local/bin/unbound-blocker.py \$ARGS

EOF

cat <<EOF > /etc/systemd/system/unbound-blocker.timer
[Unit]
Description=Run unbound-blocker every 30 minutes

[Timer]
OnBootSec=10min
OnUnitActiveSec=30min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable unbound-blocker.service
systemctl enable unbound-blocker.timer
```
