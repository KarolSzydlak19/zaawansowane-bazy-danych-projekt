import json
from faker import Faker
import random

fake = Faker('pl_PL')

class data_generator():
    def __init__(self, ROWS_PER_TABLE, data_configuration, schema):
        self.ROWS_PER_TABLE = ROWS_PER_TABLE
        self.data_configuration = self.get_gen_conf(data_configuration)
        self.schema = self.get_schema(schema)
        self.fake = fake
        
    def get_schema(self, filename):
        with open(filename, "r")as f:
            content = json.load(f)
            return content
            
    def get_gen_conf(self, filename):
        with open(filename, "r") as f:
            content = json.load(f)
            return content
    
    def get_conf_value(self, data_list):
        random_name = random.choice(
        [entry["name"] for entry in data_list]
        )
        return random_name
    
    def generate_fake_value(self, table_name, col, sql_type, data_configuration):
        table_config = data_configuration.get(table_name, {}).get("columns", {}).get(col)
        print(type(table_config))

        if not table_config:
            return self.get_fallback_value(sql_type)

        if "values" in table_config:
            return self.get_conf_value(table_config["values"])

        elif "provider" in table_config:
            provider = table_config["provider"]
            
            if hasattr(self.fake, provider):
                return str(getattr(self.fake, provider)())
            else:
                raise ValueError(f"No such provider: {provider}")

        return self.get_fallback_value(sql_type)
    
    def get_fallback_value(self, sql_type):                    
        if "VARCHAR" in sql_type or "TEXT" in sql_type:
            return "'{}'".format(fake.text(max_nb_chars=50).replace("'", "''"))
        elif "EMAIL" in sql_type:
            return f"'{fake.email()}'"
        elif "INT" in sql_type or "SERIAL" in sql_type:
            return str(random.randint(1, 100))
        elif "NUMERIC" in sql_type or "DECIMAL" in sql_type:
            return str(round(random.uniform(10, 100), 2))
        elif "TIMESTAMP" in sql_type:
            return f"'{fake.date_time_this_year().isoformat(sep=' ')}'"
        elif "DATE" in sql_type:
            return f"'{fake.date_this_year()}'"
        else:
            return "NULL"
    
    def generate_data(self):
        insert_statements = []

        for table_name, table_info in self.schema.items():
            columns_dict = table_info.get("columns", {})

            cols = [col_name for col_name, col_data in columns_dict.items() if col_data.get("type") != "SERIAL"]
            if not cols:
                continue

            for _ in range(self.ROWS_PER_TABLE):
                values = []
                for col_name in cols:
                    col_type = columns_dict[col_name].get("type")
                    val = self.generate_fake_value(table_name, col_name, col_type, self.schema)
                    values.append(val)

                col_names_str = ", ".join(cols)
                values_str = ", ".join(values)
                sql = f"INSERT INTO {table_name} ({col_names_str}) VALUES ({values_str});"
                insert_statements.append(sql)

        return insert_statements


dg = data_generator(10, "data_gen_config2.json", "parsed_schema.json")
data = dg.generate_data()
#data = dg.generate_insert_statements("data_gen_config2.json", "loactions", 10)
with open("insert_data.sql", "w") as f:
    for s in data:
        f.write(f"{s}\n")

