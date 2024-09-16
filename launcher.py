# This file runs an application and put values in cgroups according to the needs

import click
import sys
import subprocess
import os 
import psutil 
import time
import uuid


def check_pid(pid):
    if int(pid) in psutil.pids(): ## Check list of PIDs
        return True 
    else:
        return False 

def is_cgroupsv2_mounted():
    try:
        with open("/proc/self/mountinfo", "r") as f:
            for line in f:
                if "cgroup2" in line:
                    return True
        return False
    except FileNotFoundError:
        return False

def run_app_and_pid(command):
    try:
        process = subprocess.Popen([command], shell=True)
        return process
    except subprocess.CalledProcessError as e:
        print(f"Error running application: {e}")
        return None

def mount_cgroup():
    try:
        command = ["mount", "-t", "cgroup2", "-o", "none,name=systemd", "cgroup", "/sys/fs/cgroup"]
        subprocess.run(command, check=True)
        print("Successfully mounted cgroup.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to mount cgroup: {e}")
        exit()

@click.command()
@click.option('--cpubind', help='Which CPU(s) the application should be executed.')
@click.option('--memory', help='Allocate amount of memory to the application.')
@click.option('--app', required=True, prompt='Application',
              help='The application file you wish to execute.')

def run(cpubind, memory, app):
    """Simple program that runs an application in cgroupsv2 without interference."""
    CGROUP_NAME = uuid.uuid4()

    # Check if cgroupv2 is mounted in the system
    if not is_cgroupsv2_mounted():
        print("cgroups v2 is not mounted, trying to mount...")
        mount_cgroup()
    
    # Create a new directory for cgroups (error if bad)
    try:
        print("Creating groups in cgroups...")
        os.makedirs(f"/sys/fs/cgroup/{CGROUP_NAME}", exist_ok=True)
    except OSError as error:
        print("Failure, exiting application...")
        print(error)
        sys.exit(1)

    # Limit memory usage and CPU
    cpuquota = len(cpubind) * 100000
    cgroups_command = (
        f"echo '+cpu +cpuset +memory +io +pids' > /sys/fs/cgroup/cgroup.subtree_control "
        f"&& echo '+cpu +cpuset +memory +io +pids' > /sys/fs/cgroup/{CGROUP_NAME}/cgroup.subtree_control "
        f"&& echo {memory} > /sys/fs/cgroup/{CGROUP_NAME}/memory.max > /dev/null "
        f"&& echo \"{cpuquota} 100000\" > sudo tee /sys/fs/cgroup/{CGROUP_NAME}/cpu.max"
    )

    os.system(cgroups_command)

    # Apply CPU pinning if CPUs are provided
    if cpubind:
        cgroups_command =  (f"echo {cpubind} > /sys/fs/cgroup/{CGROUP_NAME}/cpuset.cpus")
        os.system(cgroups_command)
        #app_command = f"numactl --physcpubind={cpubind} {app}"
    
    app_command = app
    
    # Run application
    print(f"Running command: {app_command}")
    process = run_app_and_pid(app_command)

    if process:
        pid = process.pid

        # Put PID into the cgroups process
        os.makdirs()
        cgroups_command = f"echo {pid} > /sys/fs/cgroup/{CGROUP_NAME}/cgroup.procs"
        os.system(cgroups_command)

        # Wait process to finish
        process.wait()
        print(f"Process {pid} has finished.")
        process = False
        
    cgroups_command = f"echo > /sys/fs/cgroup/{CGROUP_NAME}/cgroup.procs"
    os.system(cgroups_command)
    print("Finished running application!")

if __name__ == '__main__':
    run()

    