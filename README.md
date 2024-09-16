# Interference-aware HPC Monitor (under development)

## What this includes?
* A modified njmon that captures performance counters for x86 processors in addition to (most) OS-level metrics located on /proc.
* Several miniapps for collecting / generating interference or isolating the application via cgroups. 
* A machine learning model for the interference prediction in a time-series, and the related data.
* A monitor which is able to detect interference.

## Requirements
* x86 processor
* InfluxDB for data collection
* Python3 and packages click, psutils
* numactl
* cpupower
For cpupower to work properly, you need to setup your GRUB start as:
```
GRUB_CMDLINE_LINUX_DEFAULT="intel_pstate=passive intel_pstate=no_hwp acpi=force" 
```


## How to use?
The basic run is:
```
sudo python3 launcher.py --ncpus [n] --cpubind [CPUIDs] --memory [AMOUNT] --app [APPLICATION]
```

Other flags:
* ```--cpufreq [MIN] [MAX]``` sets up different frequencies
* ```--collect-energy [CORE]``` displays energy differences at the end