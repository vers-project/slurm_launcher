from pathlib import Path
from experiment_launcher import parse_args

@parse_args
def myfunc(config: dict, output_dir: Path):
    print(config)
    print(output_dir)

if __name__ == "__main__":
    myfunc()