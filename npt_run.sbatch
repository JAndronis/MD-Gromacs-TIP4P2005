#!/bin/bash

#SBATCH --job-name=NPT_Equilibration
#SBATCH --partition=cops
#SBATCH --ntasks=64
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=5-00:00:00

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -o)
            WORK_DIR=$2
            shift
            shift
            ;;
        -f)
            MDP=$2
            shift
            shift
            ;;
        -p)
            TOPOL=$2
            shift
            shift
            ;;
        -g)
            CHECKPOINT=$2
            shift
            shift
            ;;
        -*|--*)
            echo "Unknown option $1"
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1") # save positional arg
            shift # past argument
            ;;
    esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

echo "OUTPUT PATH     = ${WORK_DIR}"
echo "MDP FILE        = ${MDP}"
echo "BOX             = ${BOX}"
echo "TOPOLOGY FILE   = ${TOPOL}"
echo -e "Submitting job...\n"

if [ -n "$SLURM_CPUS_PER_TASK" ]; then
    threads="$SLURM_CPUS_PER_TASK"
else
    threads=1
fi

if [ -n "$CHECKPOINT" ]; then
    cpi="-cpi $WORK_DIR/npt"
    tpr="$WORK_DIR/npt_next.tpr"
else
    cpi=""
    tpr="$WORK_DIR/npt.tpr"
    gmx grompp -f $MDP -c $WORK_DIR/nvt.gro -r $WORK_DIR/nvt.gro -p $TOPOL -o $tpr
fi

# set OpenMP
ntomp=$threads

# set environment variable
export OMP_NUM_THREADS=$threads

# run npt
if [[ "${SLURM_NNODES}" -gt "1" ]]; then
    NP="-np $SLURM_NTASKS"
    export MPIRUN="$HOME/openmpi-4.1.5/build/bin/mpirun --mca opal_warn_on_missing_libcuda 0"
    $MPIRUN $NP gmx_mpi mdrun -ntomp $ntomp -deffnm $WORK_DIR/npt -v
else
    echo $SLURM_NNODES
    NTMPI="-ntmpi $SLURM_NTASKS"
    gmx mdrun $ntmpi -ntomp $ntomp -deffnm $WORK_DIR/npt -v
fi
