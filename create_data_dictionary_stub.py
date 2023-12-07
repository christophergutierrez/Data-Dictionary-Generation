""" Create and update a table base structure in JSON format from a CSV file. """

import csv
import json
import os
from typing import List, Dict, Any
import sys
import argparse
import openai
import local_util as util


def get_table_name(file_path: str) -> str:
    """ Returns the table name from the file path. """
    base_name = os.path.basename(file_path)
    table_name, _ = os.path.splitext(base_name)
    return table_name


def generate_table_description(table_name: str, columns: List[str]) -> str:
    """ Returns a description of the table. """
    return f"{table_name}' has columns {', '.join(columns)}."


def read_csv_header(file_path: str) -> List[str]:
    """ Returns the header of the CSV file. """
    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            return next(reader)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)


def construct_json_data(table_name: str, columns: List[str]) -> Dict:
    """ Returns a JSON object with the table name, description, and columns. """
    table_description = generate_table_description(table_name, columns)
    columns_data = [
        {"Column Name": col, "Column Description": "TBD", "Column Data Notes": "TBD"}
        for col in columns
    ]

    return {
        "Table Name": table_name,
        "Table Description": table_description,
        "Columns": columns_data,
    }


def process_json_data(
    json_data: Dict[str, Any], client: openai.Client, assistant_id: str
) -> Dict[str, Any]:
    """ Returns the updated JSON data. """
    thread_id = util.create_thread(client, json.dumps(json_data), assistant_id)
    response = util.clean_json_string(util.get_response(client, thread_id))
    if response:
        try:
            return json.loads(response) if isinstance(response, str) else response
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode the JSON response: {e}\nRaw response: {response}")
    else:
        raise ConnectionError("No response received from OpenAI.")


def main(csv_file_path: str, assistant_id: str):
    """ Main function. """
    table_name = get_table_name(csv_file_path)
    columns = read_csv_header(csv_file_path)
    json_data = construct_json_data(table_name, columns)

    client = util.get_api_client()

    try:
        updated_json_data = process_json_data(json_data, client, assistant_id)
        json_file_path = f"{table_name}_base.json"
        util.write_to_file(json_file_path, json.dumps(updated_json_data, indent=4))
        print(f"Updated JSON file '{json_file_path}' has been created.")
    except Exception as e:
        print(e)
        sys.exit(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create and update a table base structure in JSON format from a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to process")
    args = parser.parse_args()

    assistant_id = os.environ.get("TABLE_DESCRIBER", "default_assistant_id")
    main(args.csv_file, assistant_id)
