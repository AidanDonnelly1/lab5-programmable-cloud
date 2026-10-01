#!/bin/bash
cd /srv

MD=http://metadata/computeMetadata/v1/instance/attributes
curl -s "$MD/vm1-launch-vm2-code" -H "Metadata-Flavor: Google" > part1.py
curl -s "$MD/vm2-startup-script" -H "Metadata-Flavor: Google" > startup.sh
curl -s "$MD/service-credentials" -H "Metadata-Flavor: Google" > service-credentials.json

apt-get update
apt-get install -y python3-pip
pip3 install google-api-python-client

export GOOGLE_APPLICATION_CREDENTIALS=/srv/service-credentials.json
python3 part1.py
