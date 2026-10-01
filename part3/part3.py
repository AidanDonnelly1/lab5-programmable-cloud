#!/usr/bin/env python3

import os

import googleapiclient.discovery
import google.oauth2.service_account as service_account

PROJECT = "lab-5-programable-cloud"
ZONE = "us-west1-a"
VM_NAME = "lab-5-vm1"
VM2_NAME = "lab-5-vm2"
HERE = os.path.dirname(os.path.abspath(__file__))


def read(path: str) -> str:
    return open(os.path.join(HERE, path)).read()


def main() -> None:
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(HERE, "service-credentials.json")
    )
    compute = googleapiclient.discovery.build("compute", "v1", credentials=credentials)

    config = {
        "name": VM_NAME,
        "machineType": f"zones/{ZONE}/machineTypes/e2-micro",
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts",
                    "diskType": f"zones/{ZONE}/diskTypes/pd-standard",
                    "diskSizeGb": "10",
                },
            }
        ],
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
        "metadata": {
            "items": [
                {"key": "startup-script", "value": read("vm1-startup.sh")},
                {"key": "vm1-launch-vm2-code", "value": read("../part1/part1.py").replace('"lab-5"', f'"{VM2_NAME}"')},
                {"key": "vm2-startup-script", "value": read("../part1/startup.sh")},
                {"key": "service-credentials", "value": read("service-credentials.json")},
            ]
        },
    }

    print("Creating instance.")
    compute.instances().insert(project=PROJECT, zone=ZONE, body=config).execute()


if __name__ == "__main__":
    main()
