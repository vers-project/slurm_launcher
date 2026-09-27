from pathlib import Path
from omegaconf import OmegaConf, DictConfig, ListConfig


def load_and_compose(config_path: Path, compose: bool = False) -> DictConfig:
    """
    Load a YAML config file.

    If compose=True, recursively merge any value that is a relative path to
    another YAML file into the parent config (original behaviour). This is
    opt-in and disabled by default to avoid accidentally treating plain path
    strings (e.g. model_config: Configs/foo.yml) as sub-configs.
    """
    cfg = OmegaConf.load(config_path)

    if not compose:
        return cfg

    current_file_dir = config_path.parent

    def resolve_recursive(node):
        if isinstance(node, DictConfig):
            for key, value in node.items():
                if _is_yaml_path(value):
                    sub_path = (current_file_dir / value).resolve()
                    node[key] = _process_sub_config(sub_path)
                else:
                    resolve_recursive(value)

        elif isinstance(node, ListConfig):
            for i, item in enumerate(node):
                if _is_yaml_path(item):
                    sub_path = (current_file_dir / item).resolve()
                    node[i] = _process_sub_config(sub_path)
                else:
                    resolve_recursive(item)

    def _is_yaml_path(value):
        return isinstance(value, str) and (value.endswith(".yaml") or value.endswith(".yml"))

    def _process_sub_config(sub_path: Path):
        if sub_path.exists():
            return load_and_compose(sub_path, compose=True)
        else:
            raise FileNotFoundError(f"Referenced config not found at: {sub_path}")

    resolve_recursive(cfg)
    return cfg
