from pydantic import BaseModel, model_validator, ConfigDict
from pathlib import Path
import pandas as pd
import sys, os

from .data import DataPipeline 
from .utils.io import load_yaml
from .utils import logger, CustomException
from .utils.functions import set_seed
from .utils.types import ( 
    ConfigType
)

from dotenv import load_dotenv
load_dotenv()

# fix seeding
set_seed(42)


class Pipeline(BaseModel): 
    """
    DESCRIPTION: main pipeline of package

    PARAMS:
    - path (Path | None): path to load .yaml file for below params configuration automatically
    - config (ConfigType | None): 

    Note: either prove arg \'path\' or \'config\'
   """
    path: Path | None = Path("config/config.yaml")
    config: ConfigType | None = None 

    # This instructs Py | Nonedantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(self): 
        try:
            logger.info("loading config...")
            if not self.config: 
                if self.path.is_file():
                    try:
                        config = load_yaml(os.getenv("CONFIG_PATH", self.path))
                        self.config = ConfigType(**config)
                        logger.info("config loaded successfully")
                    except Exception as e: 
                        raise CustomException(f"error occured while reading provided path/to/config/file {{{self.path.absolute().as_posix()}}}\n\t Error: {str(e)}", sys)
                else: 
                    raise CustomException("either provide arg \'config\' OR \'path\' path/to/.yaml file having key value pairs following .utils.types.ConfigType", sys)

            logger.info("creating config for each pipeline")
            self.create_config()

            logger.info("initializing pipelines...")
            self.data_pipeline = DataPipeline(
                config=self.data_pipeline_config
            )
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
            # data pipeline config
            self.data_pipeline_config = self.config.data

            # model pipeline config

        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

    def train(self): 
        "runs full pipeline form data ingestion to model evaluation"
        try:
            data_artifact = self.data_pipeline.run()

            return data_artifact
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

            
    def predict(self, input: pd.DataFrame): 
        "runs pipeline for model prediction"
        ...
