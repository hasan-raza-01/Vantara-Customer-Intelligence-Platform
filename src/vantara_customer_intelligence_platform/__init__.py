from pydantic import BaseModel, model_validator, ConfigDict
from pathlib import Path
import pandas as pd
import sys, os

from .data import DataPipeline 
from .utils.io import load_yaml
from .utils import logger, CustomException
from .utils.functions import set_seed
from .utils.types import DataPipelineConfigType

from dotenv import load_dotenv
load_dotenv()

# fix seeding
set_seed(42)


class Pipeline(BaseModel): 
    """
    DESCRIPTION: main pipeline of package

    PARAMS:
    Note: either prove config_path or all input variable except config_path
    - config_path (Path | None): path to load .yaml file for below params configuration automatically
    - source_uri (str | None): source uri of the file 
    - raw_data_path (Path | None): path to save final dataframe as .csv
    - schema_path (Path | None): path to save json schema 
    - delete (bool | None): True delets all previous files create in the process of making final .csv file, False leaves all file which you can see and inspect, defaults to True
    - db_name (str | None): database name to connect with postgreSQL, defaults to churn 
    - db_host (str | None): postgreSQL host address, defaults to 127.0.0.1
    - db_port (int | None): postgreSQL port to connect, defaults to 5432
    - table_name (str | None): name of table inside the database, defaults to online_retail_ii
    """
    config_path: Path | None = Path("config/config.yaml")

    # data collection config
    source_uri: str | None = None
    raw_data_path: Path | None = None
    schema_path: Path | None = None
    delete: bool | None = None
    db_name: str | None = None
    db_host: str | None = None
    db_port: int | None = None
    table_name: str | None = None

    # This instructs Py | Nonedantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(self): 
        try:
            logger.info("loading config...")
            if self.config_path.is_file():
                self.config = load_yaml(
                    os.getenv("CONFIG_PATH", self.config_path)
                )
                logger.info("config loaded successfully")
            else: 
                logger.info(f"unable to load config from <{self.config_path}>")
                if not all([
                    self.source_uri, 
                    self.raw_data_path, 
                    self.schema_path, 
                    self.db_name, 
                    self.db_host, 
                    self.db_port, 
                    self.table_name
                ]): 
                    raise CustomException("either provide ", sys)

            logger.info("creating config for each pipeline opreation")
            self.create_config()

            logger.info("initializing pipelines...")
            self.data_pipeline = DataPipeline(**self.data_pipeline_config.model_dump())

            return self
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

    def create_config(self): 
        "internal method used in initialization to create configuration for respective pipeline"
        try:
            data_collector_config = self.config["data"]["collector"]
            self.data_pipeline_config = DataPipelineConfigType(
                # data collector config
                source_uri = self.source_uri if self.source_uri else data_collector_config["source_uri"],
                raw_data_path = self.raw_data_path if self.raw_data_path else data_collector_config["raw_data_path"],
                schema_path = self.schema_path if self.schema_path else data_collector_config["schema_path"],
                delete = self.delete if isinstance(self.delete, bool) else data_collector_config["delete"],
                db_name = self.db_name if self.db_name else data_collector_config["db_name"],
                db_host = self.db_host if self.db_host else data_collector_config["db_host"],
                db_port = self.db_port if self.db_port else data_collector_config["db_port"], 
                table_name = self.table_name if self.table_name else data_collector_config["table_name"]


            )
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

    def train(self): 
        "runs full pipeline form data ingestion to model evaluation"
        try:
            logger.info("train pipeline initiated...")
            self.data_pipeline.run()

            logger.info("train pipeline completed")
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)
            
    def predict(self, input: pd.DataFrame): 
        "runs pipeline for model prediction"
        try:
            ...
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

