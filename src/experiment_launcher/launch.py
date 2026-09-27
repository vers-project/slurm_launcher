from pathlib import Path
import argparse
from omegaconf import OmegaConf
from copy import deepcopy
import datetime
import shutil
import sys
import pandas as pd

from .base_sweeper import BaseSweeper
from .configuration_sweeper import ConfigurationSweeper
from .grouped_configuration_sweeper import GroupedConfigurationSweeper
from .slurm_launcher import SlurmLauncher
from .local_launcher import LocalLauncher
from .configuration_resolver import load_and_compose


def _create_sweeper(config: dict) -> BaseSweeper:
    sweep = config.get("launcher", {}).get("sweep") or {}
    if isinstance(sweep, dict) and any(k in sweep for k in ("zip", "cartesian")):
        return GroupedConfigurationSweeper()
    return ConfigurationSweeper()


def launch():
    parser = argparse.ArgumentParser(prog="experiment_launcher")
    parser.add_argument("--config", type=Path, required=True, help="the yaml configuration of the experiment")
    parser.add_argument("--script", type=Path, required=True, help="the python script to run")
    args = parser.parse_args()

    config = dict(OmegaConf.to_object(load_and_compose(args.config)))
    output_dir = (
        Path(config["launcher"]["output_dir"])
        / datetime.datetime.now().strftime("%m-%d-%y")
        / datetime.datetime.now().strftime("%H-%M-%S")
    )
    output_dir.mkdir(parents=True)
    shutil.copy(args.config, output_dir / "config.yaml")
    sweeper = _create_sweeper(config)
    configs, sweep_combinations = sweeper.get_sweeped_configs(config)

    for config_idx, job_config in enumerate(configs):
        job_dir = output_dir / str(config_idx)
        job_dir.mkdir()
        OmegaConf.save(job_config, job_dir / "config.yaml")

    sweep_lookup = pd.DataFrame(sweep_combinations)
    sweep_lookup.insert(0, "job_index", range(len(sweep_combinations)))
    sweep_lookup.to_csv(output_dir / "sweep_lookup.csv", index=False)

    device = config["launcher"]["device_launcher"]["device"]
    if device == "slurm":
        launcher = SlurmLauncher()
    elif device == "local":
        launcher = LocalLauncher()
    else:
        raise ValueError(
            f'Device {device} is not a valid device. Supported devices: "slurm", "local"'
        )

    device_launcher_config = deepcopy(config["launcher"]["device_launcher"])
    device_launcher_config.pop("device")

    print(f"######\nLaunching {len(configs)} processe(s):")
    for sweep_combination in sweep_combinations:
        print(sweep_combination)
    print("######\n")

    launcher.submit(
        command=f"python {args.script}",
        num_jobs=len(configs),
        device_launcher_config=device_launcher_config,
        output_dir=output_dir,
    )

if __name__ == "__main__":
    launch()
