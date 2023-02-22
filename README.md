# MD-Gromacs_TIP4P-2005

An example of running water MD simulations with gromacs using TIP4P/2005

Simulating a water box based on this tutorial
<https://group.miletic.net/en/tutorials/gromacs/1-tip4pew-water/>

Here I modified CHARMM36 to add TIP4P/2005
<http://mackerell.umaryland.edu/charmm_ff.shtml>

-----

## Create topology

Make topology file (topol.top) including the following

```bash
#include "./charmm36-jul2021.ff/forcefield.itp"
#include "./charmm36-jul2021.ff/tip4p2005.itp"

[ System ]
TIP4P2005

[ Molecules]
```

## Prepare and run MD

Add water molecules

```bash
gmx solvate -cs tip4p -o box.gro -box 3 3 3 -p topol.top
```

Energy minimization

```bash
gmx grompp -f mdp/em.mdp -c box.gro -p topol.top -o em.tpr
gmx mdrun -v -deffnm em
```

NVT equilibration

```bash
gmx grompp -f mdp/nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr
gmx mdrun -deffnm nvt
```

NPT equilibration

```bash
gmx grompp -f mdp/npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr
gmx mdrun -deffnm npt
```

MD run

```bash
gmx grompp -f mdp/md.mdp -c npt.gro -t npt.cpt -p topol.top -o md_0_1.tpr
gmx mdrun -deffnm md_0_1
```

## Analyze results

Make molecules whole

```bash
gmx trjconv -s md_0_1.tpr -f md_0_1.trr -o md_0_1_noPBC.trr -pbc mol
```

Calculate O-O radial distributions

```bash
gmx rdf -f md_0_1_noPBC.trr -s md_0_1.tpr -ref 'name OW' -sel 'name OW'
```

Make index file and calculate velocity autocorrelations

```bash
gmx make_ndx -f md_0_1.gro
gmx velacc -f md_0_1_noPBC.trr -s md_0_1.tpr -n index.ndx -os -mol -recip
```

-----

## Run it on HPC

To run this on HPC see `notes.txt`. Here I use HPC2N, project number: SNIC2021-22-656.

To connect on the HPC2N use

```bash
ssh username@kebnekaise.hpc2n.umu.se
```

To activate GROMACS and it's prerequisites use:

```bash
ml GCC/10.2.0  CUDA/11.1.1  OpenMPI/4.0.5
ml GCC/10.2.0  OpenMPI/4.0.5
ml GROMACS/2021
```

Submit jobs by

```bash
sbatch slurm/cpu.sh
```

Check status by

```bash
squeue -u username
```
