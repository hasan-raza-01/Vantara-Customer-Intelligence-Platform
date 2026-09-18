from pydantic import BaseModel, model_validator, ConfigDict
import pandas as pd
import sys, os

from .data import DataPipeline 
from .utils.io import load_yaml
from .utils import logger, CustomException
from .utils.function import set_seed

from dotenv import load_dotenv
load_dotenv()

# fix seeding
set_seed(42)



class Pipeline(BaseModel): 
    """
    DESCRIPTION: main pipeline of package

    PARAMS: 
    - config (ConfigBoxType) : config for entire pipeline, defaults to None
    """
    config: dict = None
    # This instructs Pydantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')

    @model_validator(mode="after")
    def post_init(self): 
        try:
            logger.info("loading config...")
            if not self.config: 
                self.config = load_yaml(
                    os.getenv("CONFIG_PATH", "config/config.yaml")
                )

            logger.info("creating config for each pipeline opreation")
            self.create_config()

            logger.info("initializing pipelines...")
            self.data_pipeline = DataPipeline(config=self.data_config)

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
            self.data_config = self.config["data"]
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


