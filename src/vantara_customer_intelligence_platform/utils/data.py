import pandas as pd 
import sys

from . import CustomException


def generate_schema(
    df:pd.DataFrame
) -> dict[ str, tuple | dict[ str, str | dict[ str, str | int | float ] ] ]:
    """
    generates json schema of dataframe

    PARAMS: 
        - df (pd.DataFrame) : pandas data frame to generate json schema
    
    RETURNS: 
        dict[ str, tuple | dict[ str, str | dict[ str, str | int | float ] ] ]: json schema 
    """
    try:
        schema={}

        # add dataset shape
        schema["shape"]=df.shape 

        # add feature's stats
        for feature in df.columns: 
            name = feature.strip().lower()
            schema[name] = {
                "type": df[feature].dtype.name, 
                "stats": df[feature].describe().to_dict()
            }

        return schema
    except Exception as e: 
        raise CustomException(e, sys)


