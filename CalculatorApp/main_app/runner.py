import os
import subprocess
from django.conf import settings

APP_NAME = settings.EXE_PATH
FLOAT_FLAG = "--float"
INT_FLAG = ""
FLOAT_MODE = (FLOAT_FLAG, "FLOAT")
INT_MODE = (INT_FLAG, "INT")


class CalcManager:
    """
    Helper class which handles building and running calculator application

    Parameters
    ----------
        float_mode (bool): whether to run calc in FLOAT_MODE
        input_data (str): arithmetic expression passed for app to evaluate
    """
    def __init__(self, float_mode: bool, input_data: str):
        self.mode_flag, self.mode_str = FLOAT_MODE if float_mode else INT_MODE
        # convert str to bytes to pipe in stdin
        self.input_data = input_data.encode("utf-8")
        if not self._ensure_bin():
            raise Exception("Server cannot access or build app binary")
    
    def _ensure_bin(self) -> bool:
        # check if built binary exists
        if os.path.isfile(settings.EXE_PATH):
            # logger.info("Binary found in filesystem")
            return True
        # try to build from make if make exists
        if os.path.isfile(settings.MAKE_PATH):
            # logger.info("Makefile found, attempting to build binary")
            run_res = subprocess.Popen(["make", APP_NAME])
            if run_res.returncode == 0:
                # logger.info("Binary built successfully")
                return True
            else:
                # logger.error("Failed to build binary")
                return False
        #  binary and Makefile are not present in fs
        # logger.error("Binary and Makefile not found in filesystem")
        return False

    def run_app(self) -> tuple[int, str]:
        # logger.info("Running calculator application", mode=self.mode_str)
        app_process = subprocess.Popen(
            [APP_NAME, self.mode_flag],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = app_process.communicate(input=self.input_data)
        # process returns data in bytes - decode 'em and strip \n
        output = stdout.decode("utf-8").strip()
        if app_process.returncode != 0:
            raise Exception(f"Calculator application exited with code {app_process.returncode}")
        self.result = output
        # logger.info("Calculator application finished with exit code 0", output=output)
        return self.result
