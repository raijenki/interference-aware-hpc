# This file runs an application and put values in cgroups according to the needs

import click
import sys
import subprocess
import os 
import psutil 
import time
import uuid
import importlib.util
import apt



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

def sanity_check():
    # Python packages
    packages = ['psutil', 'click', 'apt']

    for package in packages:
        package = importlib.util.find_spec(package)
        if package is None:
            print(package +" is not installed")
            sys.exit(1)
    
    # APT packages (only one so far)
    package = "numactl"
    cache = apt.Cache()
    if not package in cache:
        print(package +" is not installed")
        sys.exit(1)
    
    return 0


def app_run(app):
    if app == 'stream':
        # Check if there's a stream_c in the /apps/stream folder
        if os.path.isfile("./apps/stream/stream_c"):
            return "./apps/stream/stream_c"
        else: 
            # App doesn't exist
            print("Application not found, make sure it exists by running 'make' in the rootdir, exiting...")
            sys.exit(1)

@click.command()
@click.option('--ncpus', required=True, default=0, help='Number of CPUs to be allocated')
@click.option('--cpubind', required=True, default=0, help='Which CPU(s) the application should be executed.')
@click.option('--memory', required=True, default="1G", help='Allocate amount of memory to the application.')
@click.option('--app', required=True, prompt='Application', help='The application file you wish to execute.')
@click.option('--cpufreq', nargs=2, default=[], prompt='Minimum and Minimum Frequencies for CPUs') # cpupower 
#@click.option('--collect-energy', prompt='0/1', help='The application file you wish to execute.')
#cat /sys/class/powercap/intel-rapl/intel-rapl\:0/energy_uj
# resctrl

def run(ncpus, cpubind, memory, app, cpufreq):
    """Simple program that runs an application in cgroupsv2 without interference."""
    CGROUP_NAME = uuid.uuid4()
    SUBGROUP_NAME = uuid.uuid1()

    # Check requisites (numactl, cpupower)
    sanity_check()
    # Check if applications are compiled 
    app = app_run(app)

    if cpufreq:
        minfreq, maxfreq = cpufreq
        # Set governor to userspace, set frequencies
        print(f"Setting processor frequencies to {minfreq} and {maxfreq}...")
        os.system(f"cpupower frequency-set -g userspace")
        os.system(f"cpupower frequency-set -d {minfreq} -u {maxfreq}")

    # Check if cgroupv2 is mounted in the system
    if not is_cgroupsv2_mounted():
        print("cgroups v2 is not mounted, trying to mount...")
        mount_cgroup()
    
    # Create a new directory for cgroups (error if bad)
    try:
        print("Creating groups in cgroups...")
        os.makedirs(f"/sys/fs/cgroup/{CGROUP_NAME}/{SUBGROUP_NAME}", exist_ok=True)
    except OSError as error:
        print("Failure, exiting application...")
        print(error)
        sys.exit(1)

    # Limit memory usage and CPU
    cpuquota = int(ncpus) * 100000
    cgroups_subtree = (f"echo '+cpu +cpuset +memory +io +pids' > /sys/fs/cgroup/cgroup.subtree_control")
    cgroups_cpu_max = (f"echo \"{cpuquota} 100000\" > /sys/fs/cgroup/{CGROUP_NAME}/cpu.max")
    os.system(cgroups_subtree)
    os.system(cgroups_cpu_max)
    
    if memory:
        cgroups_memory_max = (f"echo {memory} > /sys/fs/cgroup/{CGROUP_NAME}/memory.max")
        os.system(cgroups_memory_max)

    # Apply CPU pinning if CPUs are provided
    if cpubind:
        cgroups_command =  (f"echo {cpubind} > /sys/fs/cgroup/{CGROUP_NAME}/cpuset.cpus")
        os.system(cgroups_command)
        app_command = f"numactl --physcpubind={cpubind} {app}"
    else:
        app_command = app
    
    # Run application
    start = time.time()
    print(f"Running command: {app_command}")
    process = run_app_and_pid(app_command)

    if process:
        pid = process.pid

        # Put PID into the cgroups process
        print(cgroups_command)
        cgroups_command = f"echo {pid} > /sys/fs/cgroup/{CGROUP_NAME}/{SUBGROUP_NAME}/cgroup.procs"
        os.system(cgroups_command)

        # Wait process to finish
        process.wait()
        print(f"Process {pid} has finished.")
        process = False
    end = time.time()
    print("Finished running application, time = " + str(float(end-start)) + " seconds!")

if __name__ == '__main__':
    run()