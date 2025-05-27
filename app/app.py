import os
import argparse
from gen_data import data_generator
import sql_parser
import asyncio
import threading
import sys
import time


def spinner_task(stop_event):
    spinner = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{spinner[idx % len(spinner)]} Generating... ")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)


def main():
    stop_event = threading.Event()
    t = threading.Thread(target=spinner_task, args=(stop_event,))
    t.start()

    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--u', action='store_true', help='Generate configuration for data generation')
    parser.add_argument('--size', type=int, help='Datasize')
    parser.add_argument('--schema', type=str,help="SQL init file")
    abort = False
    args = parser.parse_args()

    if not args.size:
        print("Specify datasize with --size=N, where N is an integer")
        abort = True
    if not args.schema:
        print("Specify sql init file with --schema=filePath, where filePath is the path to db init file")
        abort = True

    if abort:
        return
    
    dg = data_generator(args.size, args.schema)
    data_source_path = "data_source.json"
    if args.u:
        asyncio.run(dg.gen_oai(5))
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