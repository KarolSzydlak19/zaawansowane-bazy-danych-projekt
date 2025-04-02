import os
import json


def get_data_config(filename):
    with open(filename, "r") as file:
        data = json.load(file)
        
        result = {}

    for table_name, table_data in data.items():
        table_columns = table_data.get("columns", {})
        column_dict = {}

        for column_name, column_values in table_columns.items():
            if isinstance(column_values, list):
                names = [
                    entry["name"] 
                    for entry in column_values 
                    if isinstance(entry, dict) and "name" in entry
                ]
                if names:
                    column_dict[column_name] = names

        if column_dict:
            result[table_name] = column_dict

    print(result)
    return result
get_data_config("data_gen_config.json")