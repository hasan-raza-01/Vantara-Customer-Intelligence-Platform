from pydantic import BaseModel, model_validator, ConfigDict
import sys 

from vantara_customer_intelligence_platform.utils import logger, CustomException
from .collector import DataCollector



class DataPipeline(BaseModel): 
    """
    DESCRIPTION: runs entire data pipeline
    
    PARAMS: 
    - config (ConfigBoxType) : configuration to perform pipeline
    """ 
    config: dict
    # This instructs Pydantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')
    
    @model_validator(mode="after")
    def post_init(
            self, 
    ) -> None:
        try:
            logger.info("collecting config for respective data operation...")
            self.create_config()

            logger.info("initializing all operators for data operations...")
            # initialize operators
            self.collector = DataCollector(**self.collector_config)

            logger.info("all data operators initialization complete")
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
            self.collector_config = self.config["collector"]
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)

    def run(self): 
        "runs full data pipeline"
        try: 
            self.collector.collect()
        except Exception as e: 
            logger.error(e)
            if isinstance(e, CustomException): 
                raise e 
            else: 
                raise CustomException(e, sys)


