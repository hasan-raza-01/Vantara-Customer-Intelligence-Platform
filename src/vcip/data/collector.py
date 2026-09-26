from pydantic import BaseModel, model_validator, ConfigDict
from sqlalchemy import create_engine
from urllib.request import urlretrieve
from zipfile import ZipFile
from pathlib import Path
import pandas as pd
import sys, time, os, asyncio

from vcip.utils.data import generate_schema, create_document_and_session
from vcip.utils import CustomException, logger
from vcip.utils.io import dump_json, load_json
from vcip.utils.types import (
    SqlFeaturesSchema, 
    PandasFeaturesSchema, 
    DataCollectorConfigType, 
    DataCollectorArtifacts
)


class DataCollector(BaseModel): 
    """
    DESCRIPTION: Collects data from internet using urllib.request.urlretrieve

    PARAMS: 
    - config (DataCollectorConfigType): configuration following .utils.types.DataCollectorConfigType
    """
    
    config: DataCollectorConfigType
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(
            self
    ):
        try: 
            # initialize all required variables
            self.init_vars()

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

            self.db_url = f"postgresql+psycopg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

            return self
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    def init_vars(self): 
        "internal method used to initialize all params from config"
        try:
            # input vars
            self.source_uri = self.config.source_uri
            self.raw_data_path = self.config.raw_data_path.absolute()
            self.schema_path = self.config.schema_path.absolute()
            self.delete = self.config.delete
            self.db_name = self.config.db_name
            self.db_host = self.config.db_host
            self.db_port = self.config.db_port
            self.db_user = self.config.db_user
            self.db_pass = self.config.db_pass
            self.table_name = self.config.table_name
            self.schema_table_name = self.config.schema_table_name 

            # instance vars to operate
            self.path = self.raw_data_path.parent.absolute() 
            self.path.mkdir(parents=True, exist_ok=True)
            self.cleaning_paths = [] 
            self.zip_path = self.path.joinpath(Path(self.source_uri).name).absolute()
            extracted_file_path = [self.path.joinpath(p).absolute() for p in os.listdir(self.path) if p.endswith(".xlsx")]
            self.extracted_file_path = extracted_file_path[0] if extracted_file_path else None
            self.final_data_path=self.raw_data_path.absolute()
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

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
            logger.info("downloading data...")
            start_time = time.time()

            # downlaods data from source uri and saved to zip file to provided path
            urlretrieve(self.source_uri, self.zip_path, reporthook=self.print_progress)

            download_time = time.time()-start_time
            logger.info(f"download time: {download_time:.2f} sec")

        except Exception as e: 
            logger.error(str(e)) 
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    def extract(self): 
        "internal method used to extract downloaded .zip file"
        try: 
            logger.info("extracting file...")

            # extract downloaded zip file
            with ZipFile(self.zip_path, "r") as zip_ref:
                zip_ref.extractall(self.path)
            self.cleaning_paths.append(self.zip_path)

            logger.info("extraction completed...")
            if not self.extracted_file_path:
                self.extracted_file_path = [self.path.joinpath(p).absolute() for p in os.listdir(self.path) if p.endswith(".xlsx")][0]
        except Exception as e: 
            logger.error(str(e)) 
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    def load_concat_generate(self):
        "internal method used to concatenate all sheets to create a single dataframe and generates schema"
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

            logger.info("generating schema...") 
            self.df_schema = generate_schema(self.df)

            # add extracted files to cleaning paths
            self.cleaning_paths.append(self.extracted_file_path)
        except Exception as e: 
            logger.error(str(e))
            raise CustomException(e, sys)

    async def persist(self): 
        "async func to persist concatenated DataFrame in local artifact"
        def fx(): 
            try:
                
                logger.info("persisting concatenated data...")
                start_time = time.time()
                self.df.to_csv(self.final_data_path, index=False)
                logger.info(f"time taken to persist data to local: {(time.time()-start_time):.2f} sec")

                logger.info("saving schema...")
                dump_json(self.df_schema.model_dump(), self.schema_path)

            except Exception as e: 
                if not self.final_data_path.is_file() and not self.schema_path.is_file():
                    value = "concatenated data as well as schema" 
                elif not self.final_data_path.is_file(): 
                    value = "concatenated data"
                else: 
                    value = "schema"
                logger.warning(f"failed to persist {value}, reason: {e}")
                print(CustomException(e, sys))
        return await asyncio.to_thread(fx)

    async def ingest(self): 
        "async func for data ingestion of concatenated data to postgreSQL"
        def fx(): 
            try: 
                logger.info("creating PostgreSQL engine")
                engine = create_engine(self.db_url)

                logger.info("inserting records to PostgreSQL...")
                value = "concatenated data" 
                start_time = time.time()
                self.df.to_sql(
                    name = self.table_name, 
                    con = engine, 
                    if_exists = "replace",
                    index=False,
                    dtype = SqlFeaturesSchema
                )
                logger.info(f"time taken to insert records is {(time.time()-start_time):.2f} seconds")

                logger.info("inserting schema to PostgreSQL...")
                value = "schema"
                Document, session = create_document_and_session(engine, self.schema_table_name)
                schema = load_json(
                s=dump_json(
                    data=self.df_schema.model_dump()
                )
            )
                doc = Document(
                    dataset = self.table_name, 
                    schema = schema
                )
                session.merge(doc)
                session.commit()

            except Exception as e: 
                logger.warning(f"failed to ingest {value} to postgreSQL, reason: {str(e)}")
                print(CustomException(e, sys))
        return await asyncio.to_thread(fx)
    
    async def clean(self): 
        "async func for deletes all files created throughout module process except final data file"
        def fx():
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
                logger.warning(f"failed to clean local directory, reason: {str(e)}")
                print(CustomException(e, sys))
        return await asyncio.to_thread(fx)

    def get_artifacts(self) -> DataCollectorArtifacts: 
        try:
            return DataCollectorArtifacts(
                df_=self.df, 
                schema_=self.df_schema, 
                df_path=self.final_data_path, 
                schema_path=self.schema_path
            )
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    async def io(self): 
        try: 
            await asyncio.gather(
                    asyncio.create_task(self.ingest()),
                    asyncio.create_task(self.persist()),
                    asyncio.create_task(self.clean())
                )
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    def collect(self): 
        """
        runs full process from downloading to cleaning

        this method introduces synchronocity 

        \'compute\' method can be used for computation task
         
        \'io\' method for independent io taks for data/schema persistance/ingestion, \'io\' method is dependent on \'compute\' method for internal data creation
        
        Note: only go with \'compute\' and \'io\' if having knowledge of asynchronous python
        """
        try:
            start_time = time.time()

            # compute
            self.path.mkdir(parents=True, exist_ok=True)
            self.download()
            self.extract()
            self.load_concat_generate()

            # io
            asyncio.run(self.io())
            message = f"time taken by DataCollector : {(time.time() - start_time):.1f} sec"
            print("\n", message)
            logger.info(message)

            return self.get_artifacts()
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

