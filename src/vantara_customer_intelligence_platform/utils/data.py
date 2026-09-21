import pandas as pd 
import sys

from . import CustomException
from .types import SchemaModel


def generate_schema(
    df:pd.DataFrame
) -> SchemaModel:
    """
    generates json schema of dataframe

    PARAMS: 
    - df (pd.DataFrame) : pandas data frame to generate json schema
    
    RETURNS: 
        .utils.types.SchemaModel: unified type of schema generation for dataframe
    """
    try:
        schema={}

        # add dataset shape
        schema["shape"]=df.shape 

        # add feature's stats
        for feature in df.columns: 
            name = feature.strip().lower()

            schema[name] = df[feature].describe().to_dict()
            schema[name]["type"] = df[feature].dtype.name

        return SchemaModel(**schema)
    except Exception as e: 
        raise CustomException(e, sys)


