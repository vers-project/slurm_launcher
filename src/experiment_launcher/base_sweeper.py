from abc import ABC, abstractmethod


class BaseSweeper(ABC):
    @abstractmethod
    def get_sweeped_configs(self, config: dict) -> tuple[list[dict], list[dict]]:
        """
        Returns (final_configs, sweep_combinations).

        final_configs       — one dict per job, launcher section removed, overrides applied
        sweep_combinations  — one dict per job describing which values were swept (for logging)
        """
