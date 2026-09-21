from pathlib import Path
import sys, yaml, json

from . import CustomException


def load_json(s:str | None = None, path:str | None = None) -> dict:
    """reads the data present inside the file provided in \'path\' variable

    Args:
        s (str | None): json string to reformat to dictionary, defaults to None
        path (str | None): path of the json file, defaults to None

    Returns:
        json: json of data inside file
    """
    try:
        if path and s: 
            raise ValueError("param \'s\' & \'path\' both are provided at same time, only 1 arg is supported at a time")
        elif path:
            with open(Path(path), 'r') as f:
                return json.load(f)
        else: 
            return json.loads(s)
    except Exception as e:
        raise CustomException(e, sys)

def dump_json(data:dict, path:str | None = None) -> str | None:
    """saves the dictoanary into json file

    Args:
        data (dict): dictionary data to save in form of json
        path (str | None): path to save the file, defaults to None
    """
    try:
        if path: 
            with open(Path(path), "w") as f:
                json.dump(data, fp=f, default=str, indent=4)
        else:
            return json.dumps(data, default=str, indent=4)
    except Exception as e:
        raise CustomException(e, sys)
    
def load_yaml(path:str) -> dict:
    """reads the yaml file available in path

    Args:
        path (str): path of the yaml file

    Returns:
        ConfigBox: dict["key"] = value --------->  dict.key = value
    """
    try:
        with open(Path(path), "r") as yaml_file_obj:
            return yaml.safe_load(yaml_file_obj)
    except Exception as e:
        raise CustomException(e, sys)
    
def dump_yaml(content:dict, file_path:str) -> None:
    """saves the yaml file with provided content

    Args:
        content (any): content for the yaml file
        path (str): path to save the file
    """
    try:
        with open(Path(file_path), "w") as file:
            yaml.safe_dump(content, file)
    except Exception as e:
        raise CustomException(e, sys)


