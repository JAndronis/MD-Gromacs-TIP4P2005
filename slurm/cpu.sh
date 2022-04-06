#!/bin/bash

#SBATCH -A SNIC2021-22-656
# Name of the job
#SBATCH -J GROMACS
#SBATCH -t 0-12:00:00
#SBATCH -n 28

# It is always best to do a ml purge before loading modules in a submit file
ml purge > /dev/null 2>&1

# Load the module for GROMACS and its prerequisites.
# This is for GROMACS/2016.4 with no GPU support
ml GCC/10.2.0  CUDA/11.1.1  OpenMPI/4.0.5
ml GCC/10.2.0  OpenMPI/4.0.5
ml GROMACS/2021

# Automatic selection of single or multi node based GROMACS
if [ $SLURM_JOB_NUM_NODES -gt 1 ]; then
    GMX="gmx_mpi"
    MPIRUN="mpirun"
    ntmpi=""
else
    GMX="gmx"
    MPIRUN=""
    ntmpi="-ntmpi $SLURM_NTASKS"
fi

#Automatic selection of ntomp argument based on "-c" argument to sbatch
if [ -n "$SLURM_CPUS_PER_TASK" ]; then
    ntomp="$SLURM_CPUS_PER_TASK"
else
    ntomp="1"
fi

# Make sure to set OMP_NUM_THREADS equal to the value used for ntomp
# # to avoid complaints from GROMACS
export OMP_NUM_THREADS=$ntomp

$MPIRUN $GMX mdrun $ntmpi -ntomp $ntomp -deffnm md_0_1
