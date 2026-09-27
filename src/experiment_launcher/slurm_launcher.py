from pathlib import Path
import subprocess


class SlurmLauncher:
    def __init__(self):
        self.legal_options = [
            "job-name",
            "cpus-per-task",
            "gpus-per-node",
            "nodes",
            "ntasks-per-node",
            "time",
            "constraint",
            "partition",
            "qos",
            "account",
            "open-mode",
            "setup",
            "mem",
        ]

    def write_sbatch_string(
        self,
        command: str,
        num_jobs: int,
        device_launcher_config: dict,
        output_dir: Path,
    ):
        sbatch_options_str = ""
        setup_str = ""
        for option, value in device_launcher_config.items():
            if option not in self.legal_options:
                raise ValueError(
                    f"Option {option} is not a valid slurm option, please refer to the documentation for the list of valid options"
                )
            elif option == "setup":
                for setup_cmd in value.split(";"):
                    setup_str += setup_cmd.strip() + "\n"
            else:
                sbatch_options_str += f"#SBATCH --{option}={value}\n"

        array_str = "#SBATCH --array="
        for i in range(num_jobs):
            array_str += str(i)
            if i < num_jobs - 1:
                array_str += ","

        return f"""#!/bin/bash
# parameters
{sbatch_options_str}{array_str}
#SBATCH --output={output_dir}/%a/log.out

# setup
{setup_str}

# command
srun --output {output_dir}/%a/%t_log.out {command} --config={output_dir}/$SLURM_ARRAY_TASK_ID/config.yaml --output-dir={output_dir}/$SLURM_ARRAY_TASK_ID
"""

    def write_sbatch_file(self, sbatch_string: str, sbatch_path: Path):
        with open(sbatch_path, "w") as f:
            f.write(sbatch_string)

    def submit_sbatch(self, sbatch_file: Path):
        # try:
        #     ans = subprocess.check_output(["sbatch", str(sbatch_file)], text=True)
        #     print(ans)

        # except subprocess.CalledProcessError as e:
        #     print(f"Command failed with return code {e.returncode}")

        try:
            # .run() waits for the process to complete by default.
            subprocess.run(["sbatch", str(sbatch_file)], check=True, text=True)

        except subprocess.CalledProcessError as e:
            print(f"Job failed with return code {e.returncode}")

    def submit(
        self,
        command: str,
        num_jobs: int,
        device_launcher_config: dict,
        output_dir: Path,
    ):
        sbatch_string = self.write_sbatch_string(
            command, num_jobs, device_launcher_config, output_dir
        )
        sbatch_path = output_dir / "sbatch.slurm"
        self.write_sbatch_file(sbatch_string, sbatch_path)
        self.submit_sbatch(sbatch_path)
