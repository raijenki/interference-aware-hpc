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

def get_remaining_cores(used_cores, interf_cores):
    total_cores = set(range(128))

    # Convert used cores to a set (supports individual numbers and ranges)
    used_set = set()
    interf_set = set()

    for item in used_cores:
        if isinstance(item, int):
            used_set.add(item)
        elif isinstance(item, str) and '-' in item:
            start, end = map(int, item.split('-'))
            used_set.update(range(start, end + 1))
    
    for item in interf_cores:
        if isinstance(item, int):
            interf_set.add(item)
        elif isinstance(item, str) and '-' in item:
            start, end = map(int, item.split('-'))
            interf_set.update(range(start, end + 1))
    
    # Remaining cores are the difference between all cores, used cores and interference cores
    remaining_cores = total_cores - used_set - interf_set
    sorted_cores = sorted(remaining_cores)
    string_cores = ','.join(map(str, sorted_cores))

    sorted_interf_cores = sorted(interf_cores)
    string_interf_cores = ','.join(map(str, sorted_interf_cores))

    #print(f"{used_cores} AND {string_cores}") # Sanity check
    return string_cores, string_interf_cores


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

    packages = ["intel-cmt-cat", "numactl"]
    cache = apt.Cache()
    for package in packages:
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

def read_energy_socket(socket_id):
    f = open(f"/sys/class/powercap/intel-rapl/intel-rapl:{socket_id}/energy_uj", "r")
    return f.read()
    
def create_cgroups(CGROUP_NAME, SUBGROUP_NAME, ncpus, memory, disk, cpubind):
    try:
        print("Creating groups in cgroups...")
        os.makedirs(f"/sys/fs/cgroup/{CGROUP_NAME}/{SUBGROUP_NAME}", exist_ok=True)

        # Limit memory usage and CPU
        cpuquota = int(ncpus) * 100000
        cgroups_subtree = (f"echo '+cpu +cpuset +memory +io +pids' > /sys/fs/cgroup/cgroup.subtree_control")
        cgroups_cpu_max = (f"echo \"{cpuquota} 100000\" > /sys/fs/cgroup/{CGROUP_NAME}/cpu.max")
        os.system(cgroups_subtree)
        os.system(cgroups_cpu_max)
        if memory:
            cgroups_memory_max = (f"echo {memory} > /sys/fs/cgroup/{CGROUP_NAME}/memory.max")
            os.system(cgroups_memory_max)
        if disk: 
            id, throughput = disk
            throughput_bytes = throughput * 1024 * 1024
            cgroups_io_max = (f"echo {id} rbps={throughput_bytes} > /sys/fs/cgroup/{CGROUP_NAME}/io.max")
            os.system(cgroups_io_max)
        if cpubind:
            cgroups_command =  (f"echo {cpubind} > /sys/fs/cgroup/{CGROUP_NAME}/cpuset.cpus")
            os.system(cgroups_command)

    except OSError as error:
        print("Failure, exiting application...")
        print(error)
        sys.exit(1)


@click.command()
@click.option('--ncpus', required=True, default=0, help='Number of CPUs to be allocated (cgroupv2)')
@click.option('--cpubind', required=True, help='Which CPU(s) the application should be executed (numactl).')
@click.option('--memory', required=True, default="1G", help='Allocate amount of memory to the application. (cgroupv2)')
@click.option('--app', type=click.Choice(['stream']), required=True, prompt='Application', help='The application file you wish to execute.')
@click.option('--disk', type=(str, int), required=False, help='Disk bandwidth (device, amount of MB/s).')
@click.option('--cpufreq', is_flag=False, help='Frequency for CPU')    
@click.option('--logging/--no-logging', default=False, help='If you want to log the results or not.')
@click.option('--llcisolation/--no-llc-isolation', default=False, help='If you want to log the results or not.')
@click.option('--rapl/--no-rapl', default=False, help='Measure energy using RAPL.')
@click.option('--interf', type=click.Choice(['HT', 'CPU', 'Power', 'LLC', 'Memory', 'Disk']), is_flag=False, help='The interference mode to be executed.')
def run(ncpus, cpubind, memory, app, disk, cpufreq, logging, llcisolation, rapl, interf):
    """Simple program that runs an application in cgroupsv2 without interference."""
    CGROUP_NAME = uuid.uuid4()
    SUBGROUP_NAME = uuid.uuid1()
    interf_cores = [] # For compatibility

    # This data is for the isolation study
    if interf is not None:
        interf_cores = [1,3,5,7,9,11,13]
        ncpus_interf = 8
        memory_interf = memory
        disk_interf = disk
        CGROUP_INTERF_NAME = uuid.uuid4()
        SUBGROUP_INTERF_NAME = uuid.uuid1()
        if interf == 'CPU':
            matrix_size = 10000
            reps = 20
            interf_path = "./viruses/cpu/mt-dgemm " + str(matrix_size) + " " + str(reps)
        else:
            interf_path = "sleep 10"
   
    cpu_split = [eval(i) for i in cpubind.split(",")]
    remainder_cores, interf_cores = get_remaining_cores(cpu_split, interf_cores)

    # Check requisites (numactl, cpupower, intel-cmt-cat)
    sanity_check()

    # Check if applications are compiled 
    app_path = app_run(app)

    if cpufreq:
        # Set governor to userspace, set frequencies this is not DVFS processor
        print(f"Setting processor frequencies to {cpufreq}...")
        os.system(f"cpupower frequency-set -g userspace")
        os.system(f"cpupower frequency-set -f {cpufreq}")

    # Check if cgroupv2 is mounted in the system
    if not is_cgroupsv2_mounted():
        print("cgroups v2 is not mounted, trying to mount...")
        mount_cgroup()
    
    create_cgroups(CGROUP_NAME, SUBGROUP_NAME, ncpus, memory, disk, cpubind)

    if interf is not None:
        create_cgroups(CGROUP_INTERF_NAME, SUBGROUP_INTERF_NAME, ncpus_interf, memory_interf, disk_interf, cpubind)
    
    if llcisolation:
        print("Isolating application...")
        # Set the COS bitmasks for COS1 using 50% and COS2 using 30% of cache, cores in COS0 uses the remainder
        os.system("pqos -e \"llc:0=0xFC0;llc:1=0x1C0;llc:2=0x003;llc:3=0x003;llc:4=0x003;llc:5=0x003;llc:6=0x003;llc:7=0x003;llc:8=0x003;llc:9=0x003;llc:10=0x003;llc:11=0x003;llc:12=0x003;llc:13=0x003;llc:14=0x003\"")
        # Associate each COS with the cores where each app is running
        if interf is not None:
            os.system(f"pqos -a \"llc:0={cpubind};llc:1={interf_cores};llc:2={remainder_cores}\"")
        else:
            os.system(f"pqos -a \"llc:0={cpubind};llc:1={remainder_cores}\"")

    # Apply CPU pinning if CPUs are provided
    if cpubind:
        app_command = f"numactl --physcpubind={cpubind} {app_path}"
        if interf is not None:
            interf_command = f"numactl --physcpubind={interf_cores} {interf_path}"
    else:
        app_command = app_path



    print(f"Running command: {app_command}")

    # Run application
    start = time.time()

    if rapl:
        socket0_energy_start = read_energy_socket(0)
        socket1_energy_start = read_energy_socket(1)

    process = run_app_and_pid(app_command)
    process_interf = run_app_and_pid(interf_command)

    if process:
        pid = process.pid
        pid_interf = process_interf.pid
        # Put PID into the cgroups process
        cgroups_command = f"echo {pid} > /sys/fs/cgroup/{CGROUP_NAME}/{SUBGROUP_NAME}/cgroup.procs"
        os.system(cgroups_command)

        if interf is not None:
            cgroups_command_interf = (f"echo {pid_interf} > /sys/fs/cgroup/{CGROUP_INTERF_NAME}/{SUBGROUP_INTERF_NAME}/cgroup.procs")
            os.system(cgroups_command_interf)

        # Wait process to finish
        process.wait()
        print(f"Process {pid} has finished.")
        process = False
    end = time.time()
    if rapl:
        socket0_energy_end = read_energy_socket(0)
        socket1_energy_end = read_energy_socket(1)
        energy0 = int(socket0_energy_end) - int(socket0_energy_start)
        energy1 = int(socket1_energy_end) - int(socket1_energy_start)

    print("Finished running application, time = " + str(float(end-start)) + " seconds!")
    exec_time = end - start

    # Log whatever we need
    if logging:
        if not os.path.isfile("logs.txt"):
            f = open("logs.txt", "w")
            if rapl:
                f.write("app,runtime,energy0,energy1\n")
            else:
                f.write("app,runtime\n")
            f.close()

        f = open("logs.txt", "a")
        if rapl:
            f.write(f"{app},{exec_time},{energy0},{energy1}\n")
        else:
            f.write(f"{app},{exec_time}\n")
        f.close()

    # Cleanup intel cat and cgroup
    os.system("pqos -R")
    os.system(f"rmdir /sys/fs/cgroup/{CGROUP_NAME}/{SUBGROUP_NAME}")
    os.system(f"rmdir /sys/fs/cgroup/{CGROUP_NAME}")

if __name__ == '__main__':
    run()