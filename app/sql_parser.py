import sqlparse
from faker import Faker
import json
from sqlparse.sql import Parenthesis
from sqlparse.tokens import Keyword

fake = Faker()


def read_schema(filename):
    with open(filename, "r") as file:
        schema = file.read()
    return schema

def split_line(s):
    parts = []
    current = []
    depth = 0

    for char in s:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if char == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        parts.append(''.join(current).strip())

    return parts

def extract_columns(token_list):
    columns = []
    for token in token_list:
        if isinstance(token, Parenthesis):
            inside = token.value[1:-1]
            lines = split_line(inside) #[line.strip() for line in inside.split(",") if line.strip()]
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and not parts[0].upper() in ('PRIMARY', 'FOREIGN', 'CONSTRAINT'):
                    col_name = parts[0]
                    col_type = parts[1].upper()
                    constraint = parts[2:]
                    column_data = col_type + ' ' + " ".join(constraint)
                    columns.append({"name": col_name, "type": column_data})
    return columns

def parse_schema(filename):
    schema = read_schema(filename)
    statements = sqlparse.split(schema)
    tables = {}
    
    for stmt in statements:
        parsed = sqlparse.parse(stmt)[0]
        if parsed.get_type() == 'CREATE':
            tokens = [t for t in parsed.tokens if not t.is_whitespace]
            for i, token in enumerate(tokens):
                if token.match(Keyword, 'TABLE'):
                    table_name = tokens[i + 1].get_name()
                    columns = extract_columns(tokens)
                    tables[table_name] = {"columns": columns}
                    break
    return tables
                
parsed_schema = parse_schema("../init.sql")
with open("parsed_schema.json", "w") as f:
    json.dump(parsed_schema, f, indent=4)
