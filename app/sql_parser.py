import sqlparse
from faker import Faker
import json
from sqlparse.sql import Parenthesis
from sqlparse.tokens import Keyword
import re
from collections import defaultdict, deque

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
    columns = {}
    for token in token_list:
        if isinstance(token, Parenthesis):
            inside = token.value[1:-1]
            lines = split_line(inside) 
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and not parts[0].upper() in ('PRIMARY', 'FOREIGN', 'CONSTRAINT'):
                    col_name = parts[0]
                    col_type = parts[1].upper()
                    constraint = parts[2:]
                    column_data = col_type + ' ' + " ".join(constraint)
                    provider = guess_provider(col_name)
                    #columns.append({"name": col_name, "type": column_data, "provider": provider})
                    columns[col_name] = {
                        "type" : column_data,
                        "provider": provider
                    }
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

def extract_references(column_type):
    match = re.search(r'REFERENCES\s+(\w+)\((\w+)\)', column_type, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None

# returns set, key is tablename, value is list of dependent tables             
def build_dependency_graph(tables):
    graph = defaultdict(set)
    all_tables = set(tables.keys())
    
    for table_name, table_data in tables.items():
        columns = table_data.get("columns", {})
        for column_name, column_data in columns.items():
            col_type = column_data.get("type", "")
            ref = extract_references(col_type)
            if ref:
                referenced_table = ref[0]
                if referenced_table in all_tables:
                    graph[table_name].add(referenced_table)

    #for key in graph:
        #print(f"{key}: {graph[key]}")
    return graph

def topological_sort(tables):
    graph = build_dependency_graph(tables)
    num_dependencies = {table: 0 for table in tables}
    all_tables = []
    for table in tables:
        all_tables.append(table)
    
    for table, deps in graph.items():
        for dep in deps:
            num_dependencies[table] += 1
    queue = deque([table for table, dep in num_dependencies.items() if dep == 0])
    while graph:
        if detect_cycles(graph, table):
            print("cycle")
            break
        queue_c = deque(queue)
        for table in queue_c:
            for key in list(graph.keys()):
                if table in graph[key]:
                    graph[key].remove(table)
                    if not graph[key]:
                        del graph[key]
                        queue.append(key)
    return queue

def detect_cycles(graph, all_tables):
    visited = set()
    stack = set()

    def visit(node):
        if node in stack:
            return True  # cycle
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for neighbor in graph.get(node, []):
            if visit(neighbor):
                return True
        stack.remove(node)
        return False

    return any(visit(table) for table in all_tables)

def print_generation_order_with_dependencies(tables):
    dependency_graph = build_dependency_graph(tables)
    sorted_table_queue = topological_sort(tables)

    print("Table generation order:")
    for table in sorted_table_queue:
        dependencies = dependency_graph.get(table, set())
        if dependencies:
            dep_list = ", ".join(sorted(dependencies))
            print(f" - {table} (depends on: {dep_list})")
        else:
            print(f" - {table} (no dependencies)")

def guess_provider(column_name):
    name = column_name.lower()
    if "email" in name:
        return "email"
    if "name" in name and "full" in name:
        return "name"
    if "phone" in name:
        return "phone_number"
    if "address" in name:
        return "street_address"
    if "city" in name:
        return "city"
    if "created" in name or "date" in name:
        return "date_time_this_year"
    if "price" in name:
        return "pyfloat"
    return "word"
            
parsed_schema = parse_schema("../init.sql")
with open("parsed_schema.json", "w") as f:
    json.dump(parsed_schema, f, indent=4)

#print_generation_order_with_dependencies(parsed_schema)
#dependency_graph = build_dependency_graph(parsed_schema)
topological_sort(parsed_schema)
print_generation_order_with_dependencies(parsed_schema)

