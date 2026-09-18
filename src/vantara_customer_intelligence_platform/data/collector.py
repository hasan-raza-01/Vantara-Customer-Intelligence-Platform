from pydantic import BaseModel, model_validator, ConfigDict
from urllib.request import urlretrieve
from zipfile import ZipFile
from pathlib import Path
import pandas as pd
import sys, time, os

from vantara_customer_intelligence_platform.utils import CustomException, logger
from vantara_customer_intelligence_platform.utils.data import generate_schema 
from vantara_customer_intelligence_platform.utils.io import dump_json


class DataCollector(BaseModel): 
    """
    DESCRIPTION: Collects data from internet using urllib.request.urlretrieve

    PARAMS: 
    - source_uri: source uri of the file 
    - raw_data_path: path to save final dataframe
    - schema_path: path to save json schema 
    """
    source_uri: str
    raw_data_path: Path
    schema_path: Path
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(
            self
    ) -> None:        
        self.path = self.raw_data_path.parent
        self.cleaning_paths = []
        return self

    def print_progress(self, count, block_size, total_size):
        "internal method used by 'download' method for printing download progress"
        downloaded = count * block_size
        percent = downloaded / total_size * 100
        if percent>100: 
            percent=100
        print(f"\rDownloaded: {percent:.2f}%", end='')

    def download(self): 
        "internal method used to download file from internet"
        try:  
            self.zip_path = self.path.joinpath(Path(self.source_uri).name)

            logger.info("downloading data...")
            start_time = time.time()

            # downlaods data from source uri and saved to zip file to provided path
            urlretrieve(self.source_uri, self.zip_path.absolute(), reporthook=self.print_progress)

            download_time = time.time()-start_time
            logger.info(f"download time: {download_time:.2f} sec")

        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException):
                raise e
            else: 
                raise CustomException(e, sys)

    def extract(self): 
        "internal method used to extract downloaded .zip file"
        try: 
            logger.info("extracting file...")

            # extract downloaded zip file
            with ZipFile(self.zip_path.absolute(), "r") as zip_ref:
                zip_ref.extractall(self.path.absolute())
            self.cleaning_paths.append(self.zip_path.absolute())

            logger.info("extraction completed...")
            self.extracted_file_path = [self.path.joinpath(p).absolute() for p in os.listdir(self.path) if p.endswith(".xlsx")][0]
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException):
                raise e
            else: 
                raise CustomException(e, sys)

    def concat(self):
        "internal method used to concatenate all sheets to create a single dataframe"
        try: 
            logger.info("loading data...")
            data = pd.read_excel(self.extracted_file_path.absolute(), sheet_name=None)

            logger.info("concatenating sheets...")
            self.df = pd.concat(data.values(), ignore_index=True)

            try:
                logger.info("persisting concatenated data...")
                final_data_path=self.raw_data_path.absolute()
                self.df.to_csv(final_data_path, index=False)
                logger.info("data persisted successfully")
            except Exception as e: 
                logger.warning(f"failed to persist concatenated data, reason: {e}")

            # add extracted files to cleaning paths
            self.cleaning_paths.append(self.extracted_file_path)
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException):
                raise e
            else: 
                raise CustomException(e, sys)

    def schema(self): 
        "generates schema for final dataframe"
        try:
            logger.info("generating schema...") 
            schema = generate_schema(self.df)

            logger.info("saving schema...")
            dump_json(schema, self.schema_path)
            logger.info("schema saved successfully")
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException):
                raise e
            else: 
                raise CustomException(e, sys)

    def clean(self): 
        "deletes all files created throughout module process except final data file"
        try: 
            logger.info("cleaning all unwanted files...")

            # clean all unwanted files created through out process 
            for path in set(self.cleaning_paths):
                path.unlink()

            logger.info("cleaning completed")
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException):
                raise e
            else: 
                raise CustomException(e, sys)

    def collect(self): 
        "method that runs full data collection process"
        self.path.mkdir(parents=True, exist_ok=True)
        self.download()
        self.extract()
        self.concat()
        self.schema()
        if not os.getenv("CLEAN") or os.getenv("CLEAN").lower()!="false":
            self.clean()
        else: 
            logger.info(f"ENV var \'CLEAN\' is set to \'{os.getenv("CLEAN")}\'")


