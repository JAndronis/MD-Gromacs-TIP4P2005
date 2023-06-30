#!/bin/bash

#SBATCH --job-name=Energy_Minimization
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=05:00:00

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
        -c)
            BOX=$2
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

# run em
gmx grompp -f $MDP -c $BOX -p $TOPOL -o $WORK_DIR/em.tpr
gmx mdrun -v -deffnm $WORK_DIR/em
