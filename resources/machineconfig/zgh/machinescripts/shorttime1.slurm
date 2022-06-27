#!/bin/bash
#SBATCH -J [JOB_NAME]
#SBATCH -n 1
#SBATCH -p shorttime
#SBATCH --threads-per-core=1

START=`date`
HOST=`hostname`
QNAME="compute"
echo "start: $START  $HOSTNAME  $QNAME" > start.dat
