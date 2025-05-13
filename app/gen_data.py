import json
from faker import Faker
import random

import app.sql_parser
from openai_client import oai_client
import sqlparse
import asyncio
from sqlparse.tokens import Keyword

fake = Faker('pl_PL')

class data_generator():
    def __init__(self, ROWS_PER_TABLE, data_configuration, schema):
        self.ROWS_PER_TABLE = ROWS_PER_TABLE
        self.data_configuration = self.get_gen_conf(data_configuration)
        self.schema = self.get_schema(schema)
        self.fake = fake
        self.oai_client = oai_client(ROWS_PER_TABLE)
        
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

    def read_schema(self, filename):
        with open(filename, "r") as file:
            schema = file.read()
        return schema

    def generate_insert_data(self, filename):
        statements = []
        for table_name, table_info in self.schema.items():
            columns_dict = table_info.get("columns", {})

            for _ in range(self.ROWS_PER_TABLE):
                values = []
                cols = [col_name for col_name, col_data in columns_dict.items() if "SERIAL" not in col_data.get("type")]
                for col_name in cols:
                    col_type = columns_dict[col_name].get("type")
                    ref = app.sql_parser.extract_references(col_type)
                    if ref is not None:
                        # reference assumed to be singular foreign key, with no modification
                        rand_ref = random.randint(1, self.ROWS_PER_TABLE)
                        val = f"(SELECT {ref[1]} FROM {ref[0]} WHERE {ref[1]}={rand_ref})"
                    else:
                        val_dict = self.schema[table_name].get("columns", {})[col_name]["values"]
                        val = str(random.choice(val_dict))
                        if any(ext in col_type for ext in ("VARCHAR", "TEXT", "DATE", "TIME")):
                            val = "'" + val + "'"
                    values.append(val)
                col_names_str = ", ".join(cols)
                values_str = ", ".join(values)
                sql = f"INSERT INTO {table_name} ({col_names_str}) VALUES ({values_str});"
                statements.append(sql)

        with open(filename, "w") as f:
            for s in statements:
                f.write(f"{s}\n")

    async def gen_oai(self, max_retries):
        init_schema = self.read_schema("../init.sql")
        statements = sqlparse.split(init_schema)
        for stmt in statements:
            retries = 0
            #loop in case of a corrupt response
            while retries < max_retries:
                if retries >= max_retries:
                    break

                parsed = sqlparse.parse(stmt)[0]
                if parsed.get_type() == 'CREATE':
                    tokens = [t for t in parsed.tokens if not t.is_whitespace]
                    for i, token in enumerate(tokens):
                        if token.match(Keyword, 'TABLE'):
                            table_name = tokens[i + 1].get_name()

                try:
                    response = await self.oai_client.generate_sample_data(stmt)
                    response = json.loads(response)
                    columns = self.schema[table_name].get("columns", {})
                    for col_name, values in response.items():
                        if col_name in columns:
                            columns[col_name]["values"] = values
                    break
                except Exception as e:
                    retries += 1
        with open("parsed_schema1.json", "w") as f:
            json.dump(self.schema, f, indent=4)


dg = data_generator(10, "data_gen_config.json", "parsed_schema.json")
asyncio.run(dg.gen_oai(5))
#data = dg.generate_data()
dg.generate_insert_data("insert_data.sql")
#data = dg.generate_insert_statements("data_gen_config2.json", "loactions", 10)