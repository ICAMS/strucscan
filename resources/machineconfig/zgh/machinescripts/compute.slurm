#!/bin/bash
#SBATCH -J [JOB_NAME]
#SBATCH -N [NNODES]
#SBATCH -n [NTOTALCORES]
#SBATCH -p compute
#SBATCH --threads-per-core=1

START=`date`
HOST=`hostname`
QNAME="compute"
echo "start: $START  $HOSTNAME  $QNAME" > start.dat
