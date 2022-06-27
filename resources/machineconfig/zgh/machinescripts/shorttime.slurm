#!/bin/bash
#SBATCH -J [JOB_NAME]
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -p shorttime
#SBATCH --threads-per-core=1

START=`date`
HOST=`hostname`
QNAME="compute"
echo "start: $START  $HOSTNAME  $QNAME" > start.dat
