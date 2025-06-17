import os
import argparse
from gen_data import data_generator
import sql_parser
import asyncio
import threading
import sys
import time
import requests
from sqlalchemy import create_engine

#engine = create_engine("postgresql+psycopg2://postgres:password@localhost:5433/testdb")
# postgresql+psycopg2://postgres:password@localhost:5433/cin
def spinner_task(stop_event):
    spinner = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{spinner[idx % len(spinner)]} Generating... ")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)

def is_connected():
    try:
        response = requests.get("https://www.google.com", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def main():
    if not is_connected():
        print("No internet connection, please connect to a network")
        return
    stop_event = threading.Event()
    t = threading.Thread(target=spinner_task, args=(stop_event,))
    t.start()

    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--u', type=int, help='Sample data entries in column')
    parser.add_argument('--size', type=int, help='Datasize')
    parser.add_argument('--schema', type=str,help="SQL init file")
    parser.add_argument('--db', type=str,help="DB connection string")
    abort = False
    args = parser.parse_args()
    engine = create_engine(args.db)

    if not args.size:
        print("Specifie datasize with --size=N, where N is an integer")
        abort = True
    if not args.schema:
        print("Specify sql init file with --schema=filePath, where filePath is the path to db init file")
        abort = True

    if abort:
        return
    
    dg = data_generator(args.size, args.schema, args.u, engine)
    data_source_path = "data_source.json"
    if args.u:
        asyncio.run(dg.gen_oai(args.u))
        dg.save_schema(data_source_path)

    if not os.path.exists(data_source_path):
        print(f"No datasource path, update with --u flag")
        return
    dg.get_schema(data_source_path)
    dg.generate_insert_data("insert_data.sql")
    end = time.time()
    stop_event.set()
    t.join()

    elapsed = end - start
    print(f"done in {elapsed:.2f} seconds!!!")



if __name__ == '__main__':
    main()