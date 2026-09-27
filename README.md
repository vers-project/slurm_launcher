# Experiment Launcher
## Description

This repository contains helper classes and script to launch your computer science experiments from yaml configuration files on any device (Local, Slurm clusters) easily.

This repository is highly inspired from Hydra but is simpler and easier to update to your needs. It is also faster as it doesn't implement computation heavy features of Hydra.

## Install

UV

```
uv add "git+https://github.com/quentinletellier/experiment-launcher"
```

or add this line in your ```pyproject.toml``` dependencies:
```
"git+https://github.com/quentinletellier/experiment-launcher"
```

PIP

```
pip install "git+https://github.com/quentinletellier/experiment-launcher"
```

## Features

- The launcher command takes a python script and a yaml configuration as input
- Creates a new directory with the current datetime
- Performs a parameter sweep over the provided parameter values and launches a process for each parameter combinations
- Creates an output directory for each process
- Saves a copy of the effective configuration file for each process

## Usage

```
uv run launch_experiment --script YOUR_EXP_SCRIPT.py --config YOUR_CONFIG.yaml
```

The given config should have the following structure:

```
# your experiment config
# you are free to write anything you want here

key_1:
    sub_key_1:
        value_1
key_2: value_2
key_3: value_3

# The launcher specific configuration
launcher:
  output_dir: YOUR_OUTPUT_DIR
  sweep:
    key_1.sub_key_1: [option_1, option_2, option_3]
    key_3: [option_1, option_2]
  device_launcher:
    device: slurm # "slurm" or "local"
    # slurm specific configuration
    job-name: YOUR_JOB_NAME
    cpus-per-task: 24
    gpus-per-node: 4
    ...

```

A complete yaml configuration file example is provided at 'example/config.yaml'

## Slurm config

### Legal slurm arguments:
These arguments are used as-is to create the SBATCH file. See [Slurm SBTACH documentation](https://slurm.schedmd.com/sbatch.html) for more information.
- job-name
- cpus-per-task
- gpus-per-node
- nodes
- ntasks-per-node
- time
- constraint
- qos
- account
- open-mode
- setup
- mem

### Setup option:

The "setup" option expects a string representing a bash command. This command is executed in the shell before running each process. It can be used to activate python environment, load modules on your cluster, etc...

Example:
```
setup: "module purge; module load arch/h100; module load ffmpeg; export TMPDIR=YOUR_TEMP_DIR"
```

## Parameters sweep

The ```launcher.sweep``` section of the configuration allows to run an experiment with several parameter values. Typically, this is used for grid search of hyperparameters in machine learning.

Simply name the desired parameter and indicate the list of values to test. The ```launch_experiment``` command will perform a cartesian product of the sweep parameters and run a process for each combination.

With this configuration:

```
sweep:
    key_1.sub_key_1: [option_1, option_2]
    key_3: [option_1, option_2]
```

The following combinations will be tested:

```
key_1.sub_key_1: option_1, key_3: option_1
key_1.sub_key_1: option_1, key_3: option_2
key_1.sub_key_1: option_2, key_3: option_1
key_1.sub_key_1: option_2, key_3: option_2
```

## Argument parser

The ```parse_args``` decorator can be used to automatically parse the ```--config``` and ```--output-dir``` arguments without writing the ```argparse``` code.

Simply decorate the main method in your ```YOUR_EXP_SCRIPT.py``` with it.

Example:

```
from experiment_launcher import parse_args

@parse_args
def myfunc(config: dict, output_dir: Path):
    # YOUR CODE LOGIC

if __name__ == "__main__":
    myfunc()
```

Using two arguments like this is usually sufficient for my needs. If you want to pass other arguments to your main method, don't use the decorator and define your own ```argparse``` logic.