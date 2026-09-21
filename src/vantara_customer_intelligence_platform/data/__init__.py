from pydantic import BaseModel, model_validator, ConfigDict
from pathlib import Path
import sys

from vantara_customer_intelligence_platform.utils import logger, CustomException
from .collector import DataCollector



class DataPipeline(BaseModel): 
    """
    DESCRIPTION: runs entire data pipeline
    
    PARAMS: 
    - source_uri (str): source uri of the file 
    - raw_data_path (Path): path to save final dataframe as .csv
    - schema_path (Path): path to save json schema 
    - delete (bool): True delets all previous files create in the process of making final .csv file, False leaves all file which you can see and inspect, defaults to True
    - db_name (str): database name to connect with postgreSQL, defaults to churn 
    - db_host (str): postgreSQL host address, defaults to 127.0.0.1
    - db_port (int): postgreSQL port to connect, defaults to 5432
    - table_name (str | None): name of table inside the database, defaults to online_retail_ii
    """ 
    source_uri: str
    raw_data_path: Path
    schema_path: Path
    delete: bool = True
    db_name: str = "churn"
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    table_name: str | None = "online_retail_ii"

    # This instructs Pydantic to allow arbitrary attributes to be attached at runtime
    model_config = ConfigDict(extra='allow')
    
    @model_validator(mode="after")
    def post_init(
            self, 
    ) -> None:
        try:
            logger.info("initializing all operators for data operations...")

            # initialize data collector
            self.collector = DataCollector(
                source_uri = self.source_uri,
                raw_data_path = self.raw_data_path,
                schema_path = self.schema_path,
                delete = self.delete,
                db_name = self.db_name,
                db_host = self.db_host,
                db_port = self.db_port,
                table_name= self.table_name
            )

            logger.info("all data operators initialization complete")
            return self
        
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


