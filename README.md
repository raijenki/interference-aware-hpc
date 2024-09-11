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

## How to use?
To run the application:
```
sudo python3 launcher.py --cpubind [CPUIDs] --memory [AMOUNT] --app [DIRECTORY]
```