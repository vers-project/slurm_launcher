from pathlib import Path
import subprocess

class LocalLauncher:
    def __init__(self):
        pass

    def submit(
        self,
        command: str,
        num_jobs: int,
        device_launcher_config: dict,
        output_dir: Path,
    ):
        for process_id in range(num_jobs):
            process_command = (
                command + f" --config={output_dir}/{process_id}/config.yaml --output-dir={output_dir}/{process_id}"
            )
            # try:
            #     ans = subprocess.check_output(process_command.split(" "), text=True)
            #     print(ans)

            # except subprocess.CalledProcessError as e:
            #     print(f"Command failed with return code {e.returncode}")

            try:
                # .run() waits for the process to complete by default.
                subprocess.run(process_command.split(" "), check=True, text=True)
                
            except subprocess.CalledProcessError as e:
                print(f"Job {process_id} failed with return code {e.returncode}")
                # stop loop on failure
                break

        print("All jobs completed.")