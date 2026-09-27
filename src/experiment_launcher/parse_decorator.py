from pathlib import Path
import argparse
from typing import Callable
from omegaconf import OmegaConf

from .job_timer import JobTimer


def parse_args(func: Callable):
    def wrapper():
        parser = argparse.ArgumentParser(prog="experiment_launcher")
        parser.add_argument("--config", type=Path, required=True)
        parser.add_argument("--output-dir", type=Path, required=True)
        args = parser.parse_args()

        config = OmegaConf.load(args.config)
        config = OmegaConf.to_container(config, resolve=True)

        with JobTimer(args.output_dir):
            return func(config, args.output_dir)

    return wrapper
