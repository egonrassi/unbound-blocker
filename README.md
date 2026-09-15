# unbound-blocker
Unbound Resolver middle layer to block domains from a public list without the need of a restart of the service.
This middle layer utilizes the unbound control to add and remove unwanted domains. Unwanted domains are defined to return NXdomain.

Example:
```
unbound-blocker.py --input URL1 --input URL2 --ignore ".+\.is"
```

Run it according to a timer with systemd
Define the input arguments in the environmental file found in either /etc/sysconfig or /etc/default
The environmental file should at least hold the following
```
ARGS="--input URL1 --commit"
```
An example from an Ubuntu server
```
ARGS="--input https://example.com/json.example --json --unboundsocket /run/unbound.ctl --commit"
```

Install the pip and venv packages from your repos.
Create a service account to run the service and add it to the unbound group for permissions to the control socket
```
useradd -m -s /bin/bash unbound-blocker -G unbound
```

Create a virtual environment for the user and install the requirements
```
sudo su - unbound-blocker
curl -o /home/unbound-blocker/requirements.txt https://raw.githubusercontent.com/egonrassi/unbound-blocker/main/requirements.txt
curl -o /home/unbound-blocker/unbound-blocker.py https://raw.githubusercontent.com/egonrassi/unbound-blocker/main/unbound-blocker.py
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
Now create the systemd service and timer to run the command every once in a while.

```
cat <<EOF > /etc/systemd/system/unbound-blocker.service
[Unit]
Description=unbound-blocker

[Service]
User=unbound-blocker
Group=unbound-blocker
WorkingDirectory=/home/unbound-blocker
EnvironmentFile=-/etc/sysconfig/unbound-blocker
EnvironmentFile=-/etc/default/unbound-blocker
ExecStart=/home/unbound-blocker/venv/bin/python /home/unbound-blocker/unbound-blocker.py $ARGS

[Install]
WantedBy=multi-user.target
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
