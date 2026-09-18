from functools import lru_cache
import sys, os, logging, datetime



@lru_cache
def get_logger(name: str | None = None):
    filename_format = datetime.datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
    filename = f"{filename_format}.log"
    folder_name = os.path.join(os.getcwd(), "logs")
    os.makedirs(folder_name, exist_ok=True)
    filepath = os.path.join(folder_name, filename)
    logging.basicConfig(
        level=logging.INFO,
        filename=filepath,
        filemode="a",
        format="[%(asctime)s]- %(levelname)s - %(message)s  - %(lineno)s - %(pathname)s",
        datefmt="%d/%m/%Y-%H:%M:%S")
    return logging.getLogger(name)

logger = get_logger()


class CustomException(Exception):
    def __init__(self, message, sys:sys):
        super().__init__(message)
        _, _, exc_traceback = sys.exc_info()
        file_path = exc_traceback.tb_frame.f_code.co_filename
        line_no = exc_traceback.tb_lineno
        self.mssg = f"{message}, line: {line_no}, file: {file_path}"

    def __str__(self) -> str:
        return self.mssg

