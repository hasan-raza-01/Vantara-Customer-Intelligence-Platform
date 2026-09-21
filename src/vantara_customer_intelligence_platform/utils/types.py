from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
import pandas as pd
import numpy as np
import sqlalchemy

PandasDtypeName2Class = {
    "object": np.object_, 
    "str": pd.StringDtype(storage='python', na_value=np.nan), 
    "float64": np.float64,
    "int64": np.int64, 
    "datetime64[us]": np.dtype("datetime64[us]"),
    "datetime64[ns]": np.dtype("datetime64[ns]")
}

PandasDtypeName2SqlalchemyType = {
    "object": sqlalchemy.String(), 
    "str": sqlalchemy.String(), 
    "float64": sqlalchemy.Float(),
    "int64": sqlalchemy.BigInteger(), 
    "datetime64[us]": sqlalchemy.DateTime(),
    "datetime64[ns]": sqlalchemy.DateTime()
}

PandasFeaturesSchema = {
    'Invoice': PandasDtypeName2Class["object"],
    'StockCode': PandasDtypeName2Class["object"],
    'Description': PandasDtypeName2Class["object"],
    'Quantity': PandasDtypeName2Class["int64"],
    'InvoiceDate': PandasDtypeName2Class["datetime64[us]"],
    'Price': PandasDtypeName2Class["float64"],
    'Customer ID': PandasDtypeName2Class["float64"],
    'Country': PandasDtypeName2Class["str"]
}

SqlFeaturesSchema = {
    'Invoice': PandasDtypeName2SqlalchemyType["object"],
    'StockCode': PandasDtypeName2SqlalchemyType["object"],
    'Description': PandasDtypeName2SqlalchemyType["object"],
    'Quantity': PandasDtypeName2SqlalchemyType["int64"],
    'InvoiceDate': PandasDtypeName2SqlalchemyType["datetime64[us]"],
    'Price': PandasDtypeName2SqlalchemyType["float64"],
    'Customer ID': PandasDtypeName2SqlalchemyType["float64"],
    'Country': PandasDtypeName2SqlalchemyType["str"]
}


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )


class InvoiceSchema(BaseSchema):
    count: int
    unique: int
    top: int
    freq: int
    type: str


class StockCodeSchema(BaseSchema):
    count: int
    unique: int
    top: str
    freq: int
    type: str


class DescriptionSchema(BaseSchema):
    count: int
    unique: int
    top: str
    freq: int
    type: str


class QuantitySchema(BaseSchema):
    count: float
    mean: float
    std: float
    min: float
    q25: float = Field(alias="25%")
    q50: float = Field(alias="50%")
    q75: float = Field(alias="75%")
    max: float
    type: str


class InvoiceDateSchema(BaseSchema):
    count: int
    mean: pd.Timestamp
    min: pd.Timestamp
    q25: pd.Timestamp = Field(alias="25%")
    q50: pd.Timestamp = Field(alias="50%")
    q75: pd.Timestamp = Field(alias="75%")
    max: pd.Timestamp
    type: str


class PriceSchema(BaseSchema):
    count: float
    mean: float
    std: float
    min: float
    q25: float = Field(alias="25%")
    q50: float = Field(alias="50%")
    q75: float = Field(alias="75%")
    max: float
    type: str


class CustomerIDSchema(BaseSchema):
    count: float
    mean: float
    std: float
    min: float
    q25: float = Field(alias="25%")
    q50: float = Field(alias="50%")
    q75: float = Field(alias="75%")
    max: float
    type: str


class CountrySchema(BaseSchema):
    count: int
    unique: int
    top: str
    freq: int
    type: str


class SchemaModel(BaseModel):
    invoice: InvoiceSchema
    stockcode: StockCodeSchema
    description: DescriptionSchema
    quantity: QuantitySchema
    invoicedate: InvoiceDateSchema
    price: PriceSchema
    customer_id: CustomerIDSchema = Field(alias="customer id")
    country: CountrySchema

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class DataPipelineConfigType(BaseModel): 
    source_uri: str
    raw_data_path: Path
    schema_path: Path
    delete: bool
    db_name: str
    db_host: str
    db_port: int
    table_name: str
