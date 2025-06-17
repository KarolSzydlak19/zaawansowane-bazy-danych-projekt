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
import ast



fake = Faker('pl_PL')

class data_generator():
    def __init__(self, ROWS_PER_TABLE, schema, entries_per_column, engine):
        self.ROWS_PER_TABLE = ROWS_PER_TABLE
        self.data_configuration = None
        self.schema_sql = schema
        self.schema = sql_parser.parse_schema(schema)
        self.fake = fake
        self.oai_client = oai_client(entries_per_column)
        self.engine = engine
        
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
                cols = [col_name for col_name, col_data in columns_dict.items() if "SERIAL" not in col_data.get("type") and 'PRIMARY KEY' not in col_data.get("type")]
                if len(cols) == 0:
                    continue
                for col_name in cols:
                    col_type = columns_dict[col_name].get("type")
                    ref = sql_parser.extract_references(col_type)
                    if ref is not None:
                        rand_ref = random.randint(0, self.ROWS_PER_TABLE)
                        table_name_to_check = ref[0].lower() 
                        schema_name = 'public'
                        query = f"""
SELECT
    kcu.column_name
FROM
    information_schema.table_constraints AS tc
JOIN
    information_schema.key_column_usage AS kcu
ON
    tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
    AND tc.table_name = kcu.table_name
WHERE
    tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = '{schema_name}'
    AND tc.table_name = '{table_name_to_check}';
"""

                        key_col = None
                        with self.engine.connect() as con:
                            try:
                                result = con.execute(text(query))
                                key_col = result.fetchone() 

                            except Exception as e:
                                print(f"Error executing query: {e}")
                                continue 

                            if key_col:
                                pk_column_name = key_col[0]
                        val = f"(SELECT {pk_column_name} FROM {ref[0]} ORDER BY RANDOM() LIMIT 1)"
                    else:
                        val_dict = self.schema[table_name].get("columns", {})[col_name]["values"]
                        provider = self.schema[table_name].get("columns", {})[col_name]["provider"]
                        if val_dict:
                            raw_val = random.choice(val_dict)
                        elif provider is not None:
                            parsed = parse_provider_string(provider)
                            provider_name = parsed.pop("provider")
                            try:
                                provider_func = getattr(self.fake, provider_name)
                            except Exception as e:
                                continue
                            raw_val = str(provider_func(**parsed))
                        if isinstance(raw_val, str):
                            escaped_val = raw_val.replace("'", "''")
                            val = f"'{escaped_val}'"
                        else:
                            val = str(raw_val)
                    values.append(val)
                col_names_str = ", ".join(cols)
                values_str = ", ".join(values)
                sql = f"INSERT INTO {table_name} ({col_names_str}) VALUES ({values_str});"
                statements.append(sql)
        BATCH_SIZE = self.ROWS_PER_TABLE
        with self.engine.connect() as connection:
            trans = connection.begin()
            for i, stmt in enumerate(statements):
                try:
                    connection.execute(text(stmt))
                    if (i + 1) % BATCH_SIZE == 0:
                        trans.commit()
                        trans = connection.begin()
                except Exception as e:
                    trans.rollback()
                    trans = connection.begin()
            if trans.is_active:
                trans.commit()
        with open(filename, "w") as f:
            for s in statements:
                f.write(f"{s}\n")

    async def gen_oai(self, max_retries):
        init_schema = self.read_schema(self.schema_sql)
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
                        csv_file = StringIO(response)
                        reader = csv.reader(csv_file)
                        rows = list(reader)
                        if len(rows) == 1 and len(rows[0]) == 1 and "," not in rows[0][0]:
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
                except Exception as e:
                    #print(f"Error calling OpenAI: {e}")
                    retries += 1
        with open("data_source.json", "w") as f:
            json.dump(self.schema, f, indent=4)

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
