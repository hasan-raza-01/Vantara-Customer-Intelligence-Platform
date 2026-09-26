from pydantic import BaseModel, model_validator, ConfigDict
import sys

from vcip.utils import CustomException, logger
from vcip.utils.types import DataPipelineConfigType
from .collector import DataCollector



class DataPipeline(BaseModel): 
    """
    DESCRIPTION: Collects data from internet using urllib.request.urlretrieve

    PARAMS: 
    - config (DataPipelineConfigType): configuration following .utils.types.DataPipelineConfigType
    """
    config: DataPipelineConfigType

    # This instructs Pydantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')
    
    @model_validator(mode="after")
    def post_init(
            self, 
    ) -> None:
        try:
            # initialize all params 
            self.create_config()

            # initialize data collector
            self.collector = DataCollector(
                config=self.collector_config
            )
            return self
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e
        
    def create_config(self): 
        "internal method used to create all configurations"
        try:
            self.collector_config = self.config.collector

        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

    def run(self): 
        "runs full data pipeline"
        try:
            cleaning_arfifacts = self.collector.collect()

            return cleaning_arfifacts
        except Exception as e: 
            logger.error(str(e))
            if not isinstance(e, CustomException):
                e = CustomException(e, sys)
            raise e

