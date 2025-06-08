import json
from faker import Faker
import random

import sql_parser
from openai_client import oai_client
import sqlparse
import asyncio
from sqlparse.tokens import Keyword
from sqlalchemy import create_engine, text
import re
import csv
from io import StringIO
from sqlalchemy import text

# Replace with your actual credentials
engine = create_engine("postgresql+psycopg2://postgres:password@localhost:5433/testdb")

fake = Faker('pl_PL')

class data_generator():
    def __init__(self, ROWS_PER_TABLE, schema, entries_per_column):
        self.ROWS_PER_TABLE = ROWS_PER_TABLE
        self.data_configuration = None
        self.schema = sql_parser.parse_schema(schema)
        self.fake = fake
        self.oai_client = oai_client(entries_per_column)
        
    def get_schema(self, filename):
        with open(filename, "r")as f:
            content = json.load(f)
            self.schema = content
        
    def save_schema(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.schema, file, indent=4)
            
    def get_gen_conf(self, filename):
        with open(filename, "r") as f:
            content = json.load(f)
            return content
    
    def get_conf_value(self, data_list):
        random_name = random.choice(
        [entry["name"] for entry in data_list]
        )
        return random_name
    
    # def generate_fake_value(self, table_name, col, sql_type, data_configuration):
    #     table_config = data_configuration.get(table_name, {}).get("columns", {}).get(col)
    #     print(type(table_config))

    #     if not table_config:
    #         return self.get_fallback_value(sql_type)

    #     if "values" in table_config:
    #         return self.get_conf_value(table_config["values"])

    #     elif "provider" in table_config:
    #         provider = table_config["provider"]
            
    #         if hasattr(self.fake, provider):
    #             return str(getattr(self.fake, provider)())
    #         else:
    #             raise ValueError(f"No such provider: {provider}")

    #     return self.get_fallback_value(sql_type)
    
    # def get_fallback_value(self, sql_type):                    
    #     if "VARCHAR" in sql_type or "TEXT" in sql_type:
    #         return "'{}'".format(fake.text(max_nb_chars=50).replace("'", "''"))
    #     elif "EMAIL" in sql_type:
    #         return f"'{fake.email()}'"
    #     elif "INT" in sql_type or "SERIAL" in sql_type:
    #         return str(random.randint(1, 100))
    #     elif "NUMERIC" in sql_type or "DECIMAL" in sql_type:
    #         return str(round(random.uniform(10, 100), 2))
    #     elif "TIMESTAMP" in sql_type:
    #         return f"'{fake.date_time_this_year().isoformat(sep=' ')}'"
    #     elif "DATE" in sql_type:
    #         return f"'{fake.date_this_year()}'"
    #     else:
    #         return "NULL"

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
                    ref = sql_parser.extract_references(col_type)
                    if ref is not None:
                        #reference assumed to be singular foreign key, with no modification
                        rand_ref = random.randint(0, self.ROWS_PER_TABLE)
                        val = f"(SELECT id FROM {ref[0]} ORDER BY RANDOM() LIMIT 1)"
                    else:
                        val_dict = self.schema[table_name].get("columns", {})[col_name]["values"]
                        provider = self.schema[table_name].get("columns", {})[col_name]["provider"]
                        #if isinstance(val_dict, list):
                        if val_dict:
                            raw_val = random.choice(val_dict)
                        #elif isinstance(val_dict, str):
                        else:
                            #raw_val = str(getattr(self.fake, val_dict)())
                            parsed = parse_provider_string(provider)
                            provider_name = parsed.pop("provider")
                            provider_func = getattr(self.fake, provider_name)
                            raw_val = str(provider_func(**parsed))
                        if isinstance(raw_val, str):
                            # Escape single quotes and wrap in single quotes
                            escaped_val = raw_val.replace("'", "''")
                            val = f"'{escaped_val}'"
                        else:
                            val = str(raw_val)
                    values.append(val)
                col_names_str = ", ".join(cols)
                values_str = ", ".join(values)
                sql = f"INSERT INTO {table_name} ({col_names_str}) VALUES ({values_str});"
                statements.append(sql)

        with engine.connect() as connection:
            trans = connection.begin()
            count = -1
            for stmt in statements:
                try:
                    count += 1
                    #trans = connection.begin()
                    connection.execute(text(stmt))
                    #trans.commit()
                    if(count == self.ROWS_PER_TABLE - 1):
                        trans.commit()
                        trans = connection.begin()
                        count = -1
                except Exception as e:
                    #trans.rollback()
                    print("Error:", e)
                    count -=1
                    continue

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

                #table_name_match = re.search(r'CREATE TABLE\s+(\w+)', stmt, re.IGNORECASE)
                #table_name = table_name_match.group(1) if table_name_match else None

                parsed = sqlparse.parse(stmt)[0]
                token_list = list(parsed.tokens)
                columns = sql_parser.extract_column_names(token_list)
                try:
                    for col in columns:
                        jcolumns = self.schema[table_name].get("columns", {})
                        col_name = col.split()[0]
                        if "primary" in col.lower() or "foreign" in col.lower() or "references" in col.lower():
                            jcolumns[col_name]["provider"] = None
                            continue
                        response = await self.oai_client.generate_sample_data(col)
                        #response = json.loads(response)
                        csv_file = StringIO(response)
                        reader = csv.reader(csv_file)
                        rows = list(reader)
                        if len(rows) == 1 and len(rows[0]) == 1:
                            # pojedyncza wartość = provider
                            value = rows[0][0]
                            jcolumns[col_name]["provider"] = value
                            jcolumns[col_name]["values"] = None
                        elif len(rows) == 1 and len(rows[0]) == 2:
                            joined = ", ".join(rows[0])
                            jcolumns[col_name]["provider"] = joined
                            jcolumns[col_name]["values"] = None
                        else:
                            # lista wartości = dane
                            joined = ", ".join(rows[0])
                            jcolumns[col_name]["provider"] = None
                            jcolumns[col_name]["values"] = rows[0]
                        retries = max_retries
                    # response = await self.oai_client.generate_sample_data(stmt)
                    # #response = json.loads(response)
                    # csv_file = StringIO(response)
                    # reader = csv.reader(csv_file)
                    # for row in re
                    # columns = self.schema[table_name].get("columns", {})
                    # for col_name, values in response.items():
                    #     if col_name in columns:
                    #         if isinstance(values, list):
                    #             columns[col_name]["values"] = values
                    #             columns[col_name]["provider"] = None
                    #         elif isinstance(values, str):
                    #             columns[col_name]["provider"] = values
                    #             columns[col_name]["values"] = values
                except Exception as e:
                    print(f"Error calling OpenAI: {e}")
                    retries += 1
        with open("parsed_schema1.json", "w") as f:
            json.dump(self.schema, f, indent=4)

import ast

def parse_provider_string(s: str) -> dict:
    s = s.strip()

    if "(" not in s:
        return {"provider": s}

    if not s.endswith(")"):
        raise ValueError("Invalid provider string format")

    func_name, args_str = s.split("(", 1)
    args_str = args_str.rstrip(")")

    args_dict = {}
    if args_str.strip():
        call_node = ast.parse(f"{func_name}({args_str})", mode="eval").body

        if not isinstance(call_node, ast.Call):
            raise ValueError("Parsed expression is not a function call")

        for kw in call_node.keywords:
            key = kw.arg
            value = ast.literal_eval(kw.value)
            args_dict[key] = value

    args_dict["provider"] = func_name.strip()
    return args_dict




#dg = data_generator(1000, "data_gen_config.json", "parsed_schema1.json")
# asyncio.run(dg.gen_oai(5))
#data = dg.generate_data()
#asyncio.run(dg.gen_oai(5))
#dg.save_schema("data_source.json")
#dg.generate_insert_data("insert_data.sql")
#data = dg.generate_insert_statements("data_gen_config2.json", "loactions", 10)

#dg.get_schema("data_source.json")
#dg.generate_insert_data("insert_data.sql")