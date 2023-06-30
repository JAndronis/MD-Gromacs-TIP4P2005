#!/usr/bin/env python3

import pathlib
import argparse
from datetime import datetime
import re
from shutil import copy
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gromacs run automation script")
    root = pathlib.Path(__file__).parent.parent
    mdf = pathlib.Path(root, "mdf")
    mdp = pathlib.Path(root, "mdp")
    box = pathlib.Path(root, "box.gro")
    topol = pathlib.Path(root, "topol.top")

    parser.add_argument(
        "-o", "--output-path", type=str, default=root, help="Path to output directory"
    )
    parser.add_argument(
        "-m", "--mdp", type=str, default=mdp, help="Path to mdp directory"
    )
    parser.add_argument(
        "-f", "--mdf", type=str, default=mdf, help="Path to mdf directory"
    )
    parser.add_argument(
        "-b", "--box", type=str, default=box, help="Path to configuration file"
    )
    parser.add_argument(
        "-t", "--topology", type=str, default=topol, help="Path to topology file"
    )
    parser.add_argument(
        "-p", "--partition", type=str, default="cops", help="Partition to run on"
    )
    parser.add_argument("--temp", type=int, required=True, help="Reference temperature")
    parser.add_argument("--pressure", type=int, default=1, required=True, help="Reference pressure")
    parser.add_argument(
        "--equilibration-time",
        type=int,
        default=100,
        help="Equilibration run time in nanoseconds",
    )
    parser.add_argument(
        "--production-time",
        type=int,
        default=100,
        help="Production run time in nanoseconds",
    )
    parser.add_argument("--launch", action="store_true", help="Launch run")
    parser.add_argument("--gpu", action="store_true", help="Use GPU")
    parser.add_argument(
        "--solution-name", type=str, default="water", help="Solution name"
    )

    args = parser.parse_args()
    print("OUTPUT: ", args.output_path)
    print("MDP: ", args.mdp)
    print("MDF: ", args.mdf)
    print("BOX: ", args.box)
    print("TOP: ", args.topology)
    if args.launch:
        print("Running Gromacs...")

    run_prefix = f"{args.solution_name}_{args.temp}K_{args.pressure}bar"
    current_time = datetime.now().strftime("%d-%m-%Y_%H:%M")
    output_dir = pathlib.Path(args.output_path, f"{run_prefix}_{current_time}")
    log = pathlib.Path(output_dir, "run.log")
    output_dir.mkdir()
    log.touch()

    passed_mdp_dir = pathlib.Path(args.mdp).resolve().absolute()
    temp_mdp_dir = pathlib.Path(
        f"{passed_mdp_dir}_{args.temp}K_{args.pressure}bar_temp"
    )
    temp_mdp_dir.mkdir(exist_ok=True)
    em_mdp = pathlib.Path(temp_mdp_dir, "em.mdp")
    nvt_mdp = pathlib.Path(temp_mdp_dir, "nvt.mdp")
    npt_mdp = pathlib.Path(temp_mdp_dir, "npt.mdp")
    md_mdp = pathlib.Path(temp_mdp_dir, "md.mdp")
    for f in passed_mdp_dir.iterdir():
        copy(f, temp_mdp_dir)

    temp_regex = r"^ref_t\s*=.*"
    pressure_regex = r"^ref_p\s*=.*"
    with open(nvt_mdp, "r") as f:
        ref_t = re.sub(
            temp_regex, f"ref_t = {args.temp}", f.read(), 0, flags=re.MULTILINE
        )
    with open(nvt_mdp, "w") as f:
        f.write(ref_t)
    with open(npt_mdp, "r") as f:
        ref_t = re.sub(
            temp_regex, f"ref_t = {args.temp}", f.read(), 0, flags=re.MULTILINE
        )
        ref_p = re.sub(
            pressure_regex, f"ref_p = {args.pressure}", ref_t, 0, flags=re.MULTILINE
        )
    with open(npt_mdp, "w") as f:
        f.write(ref_p)
    with open(md_mdp, "r") as f:
        ref_t = re.sub(
            temp_regex, f"ref_t = {args.temp}", f.read(), 0, flags=re.MULTILINE
        )
        ref_p = re.sub(
            pressure_regex, f"ref_p = {args.pressure}", ref_t, 0, flags=re.MULTILINE
        )
    with open(md_mdp, "w") as f:
        f.write(ref_p)

    nsteps_regex = r"^nsteps\s*=.*"
    npt_nsteps = int(args.equilibration_time * 1000 / 0.002)
    md_nsteps = int(args.production_time * 1000 / 0.002)
    with open(npt_mdp, "r") as f:
        nsteps = re.sub(
            nsteps_regex,
            f"nsteps = {npt_nsteps}  ; 0.002 * {npt_nsteps} = {args.equilibration_time} ns",
            f.read(),
            0,
            flags=re.MULTILINE,
        )
    with open(npt_mdp, "w") as f:
        f.write(nsteps)
    with open(md_mdp, "r") as f:
        nsteps = re.sub(
            nsteps_regex,
            f"nsteps = {md_nsteps}  ; 0.002 * {md_nsteps} = {args.production_time} ns",
            f.read(),
            0,
            flags=re.MULTILINE,
        )
    with open(md_mdp, "w") as f:
        f.write(nsteps)

    # Launch jobs
    if args.launch:
        scripts = pathlib.Path(__file__).parent
        if not args.gpu:
            em_script = pathlib.Path(scripts, "em_run.sbatch")
            em_run_cmd = f"sbatch -p {args.partition} --output={log} --open-mode=append --parsable {em_script} -o {output_dir} -f {em_mdp} -p {args.topology} -c {args.box}"
            em_run = subprocess.run(em_run_cmd.split(), stdout=subprocess.PIPE)
            nvt_script = pathlib.Path(scripts, "nvt_run.sbatch")
            nvt_run_cmd = f"sbatch -p {args.partition} --output={log} --open-mode=append --dependency=afterok:{em_run.stdout.decode('utf-8')} --parsable {nvt_script} -o {output_dir} -f {nvt_mdp} -p {args.topology}"
            nvt_run = subprocess.run(nvt_run_cmd.split(), stdout=subprocess.PIPE)
            npt_script = pathlib.Path(scripts, "npt_run.sbatch")
            npt_run_cmd = f"sbatch -p {args.partition} --output={log} --open-mode=append --dependency=afterok:{nvt_run.stdout.decode('utf-8')} --parsable {npt_script} -o {output_dir} -f {npt_mdp} -p {args.topology}"
            npt_run = subprocess.run(npt_run_cmd.split(), stdout=subprocess.PIPE)
            md_script = pathlib.Path(scripts, "md_run.sbatch")
            md_run_cmd = f"sbatch -p {args.partition} --output={log} --open-mode=append --dependency=afterok:{npt_run.stdout.decode('utf-8')} --parsable {md_script} -o {output_dir} -f {md_mdp} -p {args.topology}"
            md_run = subprocess.run(md_run_cmd.split(), stdout=subprocess.PIPE)
        else:
            em_run_cmd = f"sbatch -p ampere --output={log} --open-mode=append --parsable em_run.sbatch -o {output_dir} -f {em_mdp} -p {args.topology} -c {args.box}"
            em_run = subprocess.run(em_run_cmd.split(), stdout=subprocess.PIPE)
            nvt_script = pathlib.Path(scripts, "nvt_run_GPU.sbatch")
            nvt_run_cmd = f"sbatch --output={log} --open-mode=append --dependency=afterok:{em_run.stdout.decode('utf-8')} --parsable {nvt_script} -o {output_dir} -f {nvt_mdp} -p {args.topology}"
            nvt_run = subprocess.run(nvt_run_cmd.split(), stdout=subprocess.PIPE)
            npt_script = pathlib.Path(scripts, "npt_run_GPU.sbatch")
            npt_run_cmd = f"sbatch --output={log} --open-mode=append --dependency=afterok:{nvt_run.stdout.decode('utf-8')} --parsable {npt_script} -o {output_dir} -f {npt_mdp} -p {args.topology}"
            npt_run = subprocess.run(npt_run_cmd.split(), stdout=subprocess.PIPE)
            md_script = pathlib.Path(scripts, "md_run_GPU.sbatch")
            md_run_cmd = f"sbatch --output={log} --open-mode=append --dependency=afterok:{npt_run.stdout.decode('utf-8')} --parsable {md_script} -o {output_dir} -f {md_mdp} -p {args.topology}"
            md_run = subprocess.run(md_run_cmd.split(), stdout=subprocess.PIPE)
