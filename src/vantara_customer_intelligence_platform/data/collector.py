from pydantic import BaseModel, model_validator, ConfigDict
from urllib.request import urlretrieve
from sqlalchemy import create_engine
from zipfile import ZipFile
from pathlib import Path
import pandas as pd
import sys, \
        time, \
        os, \
        asyncio

from vantara_customer_intelligence_platform.utils import CustomException, logger
from vantara_customer_intelligence_platform.utils.data import generate_schema 
from vantara_customer_intelligence_platform.utils.io import dump_json
from vantara_customer_intelligence_platform.utils.types import (
    SqlFeaturesSchema, 
    PandasFeaturesSchema
)


class DataCollector(BaseModel): 
    """
    DESCRIPTION: Collects data from internet using urllib.request.urlretrieve

    PARAMS: 
    - source_uri (str): source uri of the file 
    - raw_data_path (Path): path to save final dataframe as .csv
    - schema_path (Path): path to save json schema 
    - delete (bool): True delets all previous files create in the process of making final .csv file, False leaves all file which you can see and inspect, defaults to True
    - db_name (str): database name to connect with postgreSQL, defaults to churn 
    - db_host (str):  host address of postgreSQL, defaults to 127.0.0.1
    - db_port (int): port to connect with postgreSQL, defaults to 5432
    - db_user (str | None): database username for postgreSQL to connect, default to none. Note: if None then env var \"DB_USER\" must be available or throws error
    - db_pass (str | None): database password for postgreSQL to connect, default to none. Note: if None then env var \"DB_PASSWORD\" must be available or throws error
    - table_name (str | None): name of table inside the database, defaults to online_retail_ii
    """
    
    source_uri: str
    raw_data_path: Path
    schema_path: Path
    delete: bool = True
    db_name: str = "churn"
    db_host: str = "127.0.0.1"
    db_port: int = 5432 
    db_user: str | None = None
    db_pass: str | None = None
    table_name: str | None = "online_retail_ii"
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(
            self
    ):
        try: 
            self.path = self.raw_data_path.parent 
            self.cleaning_paths = [] 

            # collect db user & password 
            if not self.db_user: 
                self.db_user = os.getenv("DB_USER")
            if not self.db_pass:
                self.db_pass = os.getenv("DB_PASSWORD")

            ## recheck for value if still None raise error
            if not self.db_user:
                raise EnvironmentError("no database user provided, either provide in input param \"db_user\" or set env var \"DB_USER\"")
            if not self.db_pass: 
                raise EnvironmentError(f"no password provided for user \"{self.db_user}\", either  provide in input param \"db_pass\" or set env var \"DB_PASSWORD\"")

            # create db connection url 
            self.db_url = f"postgresql+psycopg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

            return self
        except Exception as e: 
            logger.error(str(e))
            raise CustomException(e, sys)

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
            logger.error(str(e))
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
            logger.error(str(e))
            raise CustomException(e, sys)

    def concat(self):
        "internal method used to concatenate all sheets to create a single dataframe"
        try: 

            logger.info("loading data...")
            # Extract the regular types and date columns dynamically from your schema dictionary
            regular_dtypes = {col: dt for col, dt in PandasFeaturesSchema.items() if not str(dt).startswith('datetime')}
            date_columns = [col for col, dt in PandasFeaturesSchema.items() if str(dt).startswith('datetime')]
            data = pd.read_excel(
                self.extracted_file_path.absolute(), 
                sheet_name=None, 
                dtype=regular_dtypes, 
                parse_dates=date_columns
                )
            logger.info("concatenating sheets...")
            self.df = pd.concat(data.values(), ignore_index=True)

            # add extracted files to cleaning paths
            self.cleaning_paths.append(self.extracted_file_path)
        except Exception as e: 
            logger.error(str(e))
            raise CustomException(e, sys)

    async def persist_data(self): 
        "async func to persist concatenated DataFrame in local artifact"
        def fx(): 
            try:
                logger.info("persisting concatenated data...")
                self.final_data_path=self.raw_data_path.absolute()
                start_time = time.time()
                self.df.to_csv(self.final_data_path, index=False)
                logger.info(f"time taken to persist data to local: {(time.time()-start_time):.2f} sec")

            except Exception as e: 
                logger.warning(f"failed to persist concatenated data, reason: {e}")
        return await asyncio.to_thread(fx)

    async def ingest(self): 
        "async func for data ingestion of concatenated data to postgreSQL"
        def fx(): 
            try: 
                logger.info("creating PostgreSQL engine")
                engine = create_engine(self.db_url)

                logger.info("inserting records to PostgreSQL...")
                start_time = time.time()
                self.df.to_sql(
                    name = self.table_name, 
                    con = engine, 
                    if_exists = "replace",
                    index=False,
                    dtype = SqlFeaturesSchema
                )
                logger.info(f"time taken to insert records is {(time.time()-start_time):.2f} seconds")
            except Exception as e: 
                logger.warning(f"failed to ingest data to postgreSQL, reason: {str(e)}")
        return await asyncio.to_thread(fx)
    
    async def schema_generation(self): 
        "generates schema for final dataframe and persist to local artifact"
        def fx():
            try:
                logger.info("generating schema...") 
                schema = generate_schema(self.df)
                logger.info("saving schema...")
                dump_json(schema.model_dump(), self.schema_path)

                logger.info("schema saved successfully")
            except Exception as e: 
                logger.error(str(e))
                raise CustomException(e, sys)
        return await asyncio.to_thread(fx)
    
    def clean(self): 
        "deletes all files created throughout module process except final data file"
        try: 
            if self.delete:
                logger.info("cleaning all unwanted files...")

                # clean all unwanted files created through out process 
                for path in set(self.cleaning_paths):
                    path.unlink()

                logger.info("cleaning completed")
            else: 
                logger.info("user choosen not to clean, not cleaning directory")
        except Exception as e: 
            logger.error(str(e))
            raise CustomException(e, sys)

    async def main(self): 
        "method that runs full data collection process"
        self.path.mkdir(parents=True, exist_ok=True)
        self.download()
        self.extract()
        self.concat()
        await asyncio.gather(
            self.persist_data(),
            self.ingest(),
            self.schema_generation(),
        )
        self.clean()

    def collect(self): 
        start_time = time.time()

        asyncio.run(self.main())
        
        time_taken = time.time() - start_time
        message = f"total time taken by DataCollector: {time_taken:.2f} sec"
        print("\n", message)
        logger.info(message)

