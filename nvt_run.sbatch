#!/bin/bash

#SBATCH --job-name=NVT_equilibration
#SBATCH --partition=cops
#SBATCH --ntasks=64
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=2-00:00:00

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

export GMX_ENABLE_DIRECT_GPU_COMM=1

if [ -n "$SLURM_CPUS_PER_TASK" ]; then
    ntomp="$SLURM_CPUS_PER_TASK"
else
    ntomp="1"
fi

if [ -n "$CHECKPOINT" ]; then
    cpi="-cpi $WORK_DIR/nvt"
    tpr="$WORK_DIR/nvt_next.tpr"
else
    cpi=""
    tpr="$WORK_DIR/nvt.tpr"
    gmx grompp -f $MDP -c $WORK_DIR/em.gro -r $WORK_DIR/em.gro -p $TOPOL -o $tpr
fi

export OMP_NUM_THREADS=$ntomp

# gmx_mpi grompp -f $MDP -c $WORK_DIR/em.gro -r $WORK_DIR/em.gro -p $TOPOL -o $WORK_DIR/nvt.tpr
# mpirun -np $SLURM_NTASKS gmx_mpi mdrun -ntomp $ntomp -v -deffnm $WORK_DIR/nvt -pin on -npme 1

if [[ "${SLURM_NNODES}" -gt "1" ]]; then
    export MPIRUN="$HOME/openmpi-4.1.5/build/bin/mpirun --mca opal_warn_on_missing_libcuda 0"
    $MPIRUN -np $SLURM_NTASKS gmx_mpi mdrun -v -ntomp $ntomp -deffnm $WORK_DIR/nvt -npme -1
else
    gmx mdrun -v -ntmpi $SLURM_NTASKS -ntomp $ntomp -deffnm $WORK_DIR/nvt -npme -1
fi
