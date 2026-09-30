#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
import google.auth

PROJECT = "lab-5-programable-cloud"
ZONE = "us-west1-a"
VM_NAME = "lab-5"

#
# Stub code - just lists all instances
#
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

# START From https://github.com/GoogleCloudPlatform/python-docs-samples/blob/c31c5866a088f4aa47ef1d87e26aefd04da08529/compute/api/create_instance.py
def create_instance(
    compute: object,
    project: str,
    zone: str,
    name: str,
) -> str:
    """Creates an instance in the specified zone.

    Args:
      compute: an initialized compute service object.
      project: the Google Cloud project ID.
      zone: the name of the zone in which the instances should be created.
      name: the name of the instance.

    Returns:
      The instance object.
    """
    
    startup_script = open(
        os.path.join(os.path.dirname(__file__), "startup.sh")
    ).read()
    
    config = {
              "name": name,
              "machineType": f"zones/{zone}/machineTypes/e2-micro",
              "disks": [
                {
                  "boot": True,
                  "autoDelete": True,
                  "initializeParams": {
                    "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts",
                    "diskType": f"zones/{zone}/diskTypes/pd-standard",
                    "diskSizeGb": "10"
                  }
                }
              ],
              "networkInterfaces": [
                {
                  "network": "global/networks/default",
                  "accessConfigs": [
                    { "type": "ONE_TO_ONE_NAT", "name": "External NAT" }
                  ]
                }
              ],
              "serviceAccounts": [
                {
                  "email": "default",
                  "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_only",
                    "https://www.googleapis.com/auth/logging.write"
                  ]
                }
              ],
              "metadata": {
                "items": [
                    {"key": "startup-script", "value": startup_script}
                ]
              }
            }

    return compute.instances().insert(project=project, zone=zone, body=config).execute()


# [END compute_create_instance]
# [START compute_wait_for_operation]

def wait_for_operation(
    compute: object,
    project: str,
    zone: str,
    operation: str,
) -> dict:
    """Waits for the given operation to complete.

    Args:
      compute: an initialized compute service object.
      project: the Google Cloud project ID.
      zone: the name of the zone in which the operation should be executed.
      operation: the operation ID.

    Returns:
      The result of the operation.
    """
    print("Waiting for operation to finish...")
    while True:
        result = (
            compute.zoneOperations()
            .get(project=project, zone=zone, operation=operation)
            .execute()
        )

        if result["status"] == "DONE":
            print("done.")
            if "error" in result:
                raise Exception(result["error"])
            return result

        time.sleep(1)


# [END compute_wait_for_operation]
# END From https://github.com/GoogleCloudPlatform/python-docs-samples/blob/c31c5866a088f4aa47ef1d87e26aefd04da08529/compute/api/create_instance.py


def main() -> None:
    compute = googleapiclient.discovery.build("compute", "v1")

    print("Creating instance.")

    op = create_instance(compute, PROJECT, ZONE, VM_NAME)
    wait_for_operation(compute, PROJECT, ZONE, op["name"])
         
    
    result = compute.firewalls().list(project=PROJECT, filter='name="allow-5000"').execute()
    
    if "items" not in result:
        firewall_body = {
            "name": "allow-5000",
            "network": "global/networks/default",
            "direction": "INGRESS",
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": ["allow-5000"],
            "allowed": [{"IPProtocol": "tcp", "ports": ["5000"]}],
        }
            
        op = compute.firewalls().insert(project=PROJECT, body=firewall_body).execute()
        while True:
            fw_op = compute.globalOperations().get(project=PROJECT, operation=op["name"]).execute()
            if fw_op["status"] == "DONE":
                if "error" in fw_op:
                    raise Exception(fw_op["error"])
                break
            time.sleep(1)
    else:
        print("Firewall rule allow-5000 already exists.")
        instance = compute.instances().get(project=PROJECT, zone=ZONE, instance=VM_NAME).execute()
        fingerprint = instance["tags"]["fingerprint"]
        op = compute.instances().setTags(
            project=PROJECT,
            zone=ZONE,
            instance=VM_NAME,
            body={"items": ["allow-5000"], "fingerprint": fingerprint},
        ).execute()
        wait_for_operation(compute, PROJECT, ZONE, op["name"])
    
        # Print the URL
        instance = compute.instances().get(project=PROJECT, zone=ZONE, instance=VM_NAME).execute()
        ip = instance["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        print(f"\nThe Flask application will be available in a few minutes at:\nhttp://{ip}:5000")


if __name__ == "__main__":
    main()