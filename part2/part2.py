#!/usr/bin/env python3

import os
import time

import googleapiclient.discovery
from googleapiclient.errors import HttpError

PROJECT = "lab-5-programable-cloud"
ZONE = "us-west1-a"
VM_NAME = "lab-5"
SNAPSHOT_NAME = f"base-snapshot-{VM_NAME}"
CLONE_NAMES = [f"{VM_NAME}-clone-{i}" for i in range(1, 4)]


# START From https://github.com/GoogleCloudPlatform/python-docs-samples/blob/c31c5866a088f4aa47ef1d87e26aefd04da08529/compute/api/create_instance.py
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
# END From https://github.com/GoogleCloudPlatform/python-docs-samples/blob/c31c5866a088f4aa47ef1d87e26aefd04da08529/compute/api/create_instance.py


def create_instance_from_snapshot(compute: object, name: str) -> dict:
    config = {
        "name": name,
        "machineType": f"zones/{ZONE}/machineTypes/e2-micro",
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceSnapshot": f"global/snapshots/{SNAPSHOT_NAME}",
                    "diskType": f"zones/{ZONE}/diskTypes/pd-standard",
                },
            }
        ],
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
    }
    return compute.instances().insert(project=PROJECT, zone=ZONE, body=config).execute()


def main() -> None:
    compute = googleapiclient.discovery.build("compute", "v1")

    try:
        compute.snapshots().get(project=PROJECT, snapshot=SNAPSHOT_NAME).execute()
        print(f"Snapshot {SNAPSHOT_NAME} already exists.")
    except HttpError as e:
        if e.resp.status != 404:
            raise
        instance = compute.inspstances().get(project=PROJECT, zone=ZONE, instance=VM_NAME).execute()
        disk = instance["disks"][0]["source"].split("/")[-1]
        print(f"Creating snapshot {SNAPSHOT_NAME} from disk {disk}.")
        op = compute.disks().createSnapshot(
            project=PROJECT, zone=ZONE, disk=disk, body={"name": SNAPSHOT_NAME}
        ).execute()
        wait_for_operation(compute, PROJECT, ZONE, op["name"])

    timings = []
    for name in CLONE_NAMES:
        print(f"Creating instance {name}.")
        start = time.time()
        op = create_instance_from_snapshot(compute, name)
        wait_for_operation(compute, PROJECT, ZONE, op["name"])
        elapsed = time.time() - start
        print(f"{name} took {elapsed:.2f} seconds.")
        timings.append((name, elapsed))

    with open(os.path.join(os.path.dirname(__file__), "TIMING.md"), "w") as f:
        f.write(f"# Instance creation times from `{SNAPSHOT_NAME}`\n\n")
        f.write("| Instance | Time (seconds) |\n|---|---|\n")
        for name, elapsed in timings:
            f.write(f"| {name} | {elapsed:.2f} |\n")


if __name__ == "__main__":
    main()
