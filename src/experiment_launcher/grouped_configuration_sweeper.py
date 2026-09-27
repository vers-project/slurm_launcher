from copy import deepcopy
from itertools import product as cartesian_product

from .base_sweeper import BaseSweeper


class GroupedConfigurationSweeper(BaseSweeper):
    """
    Sweeper for the grouped zip+cartesian format:

        launcher:
          sweep:
            zip:
              <group_name>:          # label only, not written to configs
                - {param_a: v1, param_b: v2}
                - {param_a: v3, param_b: v4}
              <other_group>:
                - {param_c: x}
                - {param_c: y}
            cartesian:
              param_d: [p, q]

    Final jobs = cartesian product of (one choice per zip group) x (all cartesian combos).
    Both zip choice dicts and cartesian keys support dot-path notation (e.g. "model.lr").
    """

    def _expand_zip_groups(self, zip_groups: dict) -> list[dict]:
        """One merged dict per combination, taking one choice from each zip group."""
        if not zip_groups:
            return [{}]
        groups = list(zip_groups.values())
        result = []
        for chosen in cartesian_product(*groups):
            merged: dict = {}
            for choice in chosen:
                merged.update(choice)
            result.append(merged)
        return result

    def _expand_cartesian(self, cartesian_params: dict) -> list[dict]:
        """One dict per combination of the independent param lists."""
        if not cartesian_params:
            return [{}]
        keys = list(cartesian_params.keys())
        result = []
        for values in cartesian_product(*cartesian_params.values()):
            result.append(dict(zip(keys, values)))
        return result

    def _cross_combine(
        self, zip_combos: list[dict], cartesian_combos: list[dict]
    ) -> list[dict]:
        """Cartesian product of the two combo lists, merging each pair into one dict."""
        result = []
        for z, c in cartesian_product(zip_combos, cartesian_combos):
            merged = deepcopy(z)
            merged.update(c)
            result.append(merged)
        return result

    def _apply_overrides(self, base_config: dict, overrides: dict) -> dict:
        config = deepcopy(base_config)
        for dot_path, value in overrides.items():
            node = config
            parts = dot_path.split(".")
            for part in parts[:-1]:
                node = node[part]
            node[parts[-1]] = value
        return config

    def _strip_launcher(self, config: dict) -> dict:
        config = deepcopy(config)
        config.pop("launcher")
        return config

    def get_sweeped_configs(self, config: dict) -> tuple[list[dict], list[dict]]:
        config = deepcopy(config)
        sweep = config["launcher"].get("sweep") or {}

        zip_groups = sweep.get("zip") or {}
        cartesian_params = sweep.get("cartesian") or {}

        zip_combos = self._expand_zip_groups(zip_groups)
        cartesian_combos = self._expand_cartesian(cartesian_params)
        all_combinations = self._cross_combine(zip_combos, cartesian_combos)

        base_config = self._strip_launcher(config)
        configs = [self._apply_overrides(base_config, combo) for combo in all_combinations]

        return configs, all_combinations
