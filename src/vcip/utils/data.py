from sqlalchemy.orm import declarative_base, sessionmaker 
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
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

def create_document_and_session(engine, table_name:str = "schema") -> tuple: 
    """creates document type with \'table_name\' and session connected with \'table_name\' through \'engine\'
    
    PARAMS: 
    - engine (sqlalchemy.create_engine(url)) : sqlalchemy engine to connect with database
    - table_name (str) : name of the table to create and store data in Document format
    
    RETURNS: 
    - Document: class to create document for insertion 
    - session: session connected with table
    """
    Base = declarative_base()
    class Document(Base):
        __tablename__ = table_name
        dataset = Column(String, primary_key=True)
        schema = Column(JSONB)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)()
    return ( Document, Session )

