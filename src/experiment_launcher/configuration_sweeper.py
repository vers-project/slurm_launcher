from copy import deepcopy

from .base_sweeper import BaseSweeper


class ConfigurationSweeper(BaseSweeper):
    def __init__(self):
        pass

    def get_sweep_combinations(self, sweep_parameters: dict):
        old = [{}]
        for key, value_list in sweep_parameters.items():
            new = []
            for config in old:
                for value in value_list:
                    new_config = deepcopy(config)
                    new_config[key] = value
                    new.append(new_config)
            old = new
        return old

    def get_sub_config_from_dot_path(self, config: dict, dot_path: str):
        sub_config = config
        for sub_path in dot_path.split(".")[:-1]:
            sub_config = sub_config[sub_path]
        return sub_config

    def replace_sweep_parameters(self, config: dict, sweep_combination: dict):
        config = deepcopy(config)
        for key, value in sweep_combination.items():
            self.get_sub_config_from_dot_path(config, key)[key.split(".")[-1]] = value
        return config

    def remove_launcher_from_config(self, config: dict):
        config = deepcopy(config)
        config.pop("launcher")
        return config

    def get_sweeped_configs(self, config: dict):
        config = deepcopy(config)

        if "sweep" in config["launcher"] and config["launcher"]["sweep"] is None:
            config["launcher"].pop("sweep")

        sweep_combinations = self.get_sweep_combinations(
            config["launcher"].get("sweep", {})
        )
        configs = []
        for sweep_combination in sweep_combinations:
            sweeped_config = self.replace_sweep_parameters(
                self.remove_launcher_from_config(config), sweep_combination
            )
            configs.append(sweeped_config)
        return configs, sweep_combinations
