""" Generates summary statistics from a CSV file. """

import json
import sys
import os
from typing import Any, Dict, List
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_df(df: pd.DataFrame) -> pd.DataFrame:
    """Converts data types of a DataFrame columns to appropriate types."""
    # Using DataFrame applymap for more efficient type conversion
    def convert_element(x):
        if pd.api.types.is_integer_dtype(x):
            return float(x) if pd.notna(x) else None
        if pd.api.types.is_string_dtype(x):
            return str(x)
        return x

    return df.applymap(convert_element)


def get_column_data_type(column: pd.Series) -> str:
    """ Returns the data type of a column as a string. """
    return column.dtype


def count_unique_values(column: pd.Series) -> int:
    """ Returns the number of unique values in a column. """
    return column.nunique()


def count_missing_values(column: pd.Series) -> int:
    """ Returns the number of missing values in a column. """
    return column.isna().sum()


def calculate_summary_statistics(column: pd.Series) -> Dict[str, float]:
    """ Returns a dictionary of summary statistics for a numeric column. """
    if pd.api.types.is_numeric_dtype(column):
        return {
            "mean": column.mean(),
            "median": column.median(),
            "std": column.std(),
            "min": column.min(),
            "max": column.max(),
        }
    raise TypeError(f"Column data type must be numeric, received: {column.dtype}")


def get_sample_entries(column: pd.Series, sample_size: int = 5) -> List[Any]:
    """ Returns a list of sample entries from a column. """
    return column.sample(n=sample_size).tolist()


def calculate_deciles(column: pd.Series, n: int = 10) -> Dict[str, float]:
    """ Returns a dictionary of deciles for a numeric column. """
    deciles = {f"{(i+1)*10}%": column.quantile(i / 10) for i in range(n - 1)}
    return deciles


def get_top_n_values(column: pd.Series, top_n: int = 10) -> Dict[Any, int]:
    """ Returns a dictionary of top n values and their counts for a string column. """
    return column.value_counts().head(top_n).to_dict()


def prepare_column_summary(
    df: pd.DataFrame, top_n: int = 10
) -> Dict[str, Dict[str, Any]]:
    """ Returns a dictionary of column summaries for a DataFrame. """
    summary = {}
    for column_name in df.columns:
        column = df[column_name]
        summary[column_name] = {
            "column_name": column_name,
            "data_type": get_column_data_type(column),
            "unique_values_count": count_unique_values(column),
            "missing_values_count": count_missing_values(column),
            "sample_entries": get_sample_entries(column),
        }
        if pd.api.types.is_numeric_dtype(column):
            summary[column_name]["summary_statistics"] = calculate_summary_statistics(
                column
            )
            summary[column_name]["deciles"] = calculate_deciles(column, n=top_n)
        elif pd.api.types.is_string_dtype(column):
            summary[column_name]["top_n_values"] = get_top_n_values(column, top_n=top_n)
        else:
            summary[column_name]["summary_statistics"] = {}
    return summary


def default_converter(o: Any) -> Any:
    """ Converts objects to JSON serializable format. """
    if isinstance(o, (pd.Int64Dtype, pd.Float64Dtype, pd.BooleanDtype, pd.StringDtype)):
        return o.name
    if isinstance(o, pd.Series):
        return o.astype("object").where(o.notnull(), None).tolist()
    if isinstance(o, (pd.Timestamp, np.datetime64)):
        return o.isoformat()
    if isinstance(o, (np.integer, np.floating, np.bool_)):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Index)):
        return o.tolist()
    if isinstance(o, pd._libs.missing.NAType):
        return None
    if isinstance(o, pd.NA.__class__):
        return None
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def write_dict_to_json(data: dict, file_name: str) -> None:
    """ Writes a dictionary to a JSON file. """
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4, default=default_converter)
    except TypeError as e:
        logging.error(f"Failed to write the dictionary to JSON file '{file_name}': %s", e)
        raise


def read_table(file_path: str) -> pd.DataFrame:
    """ Reads a table from a CSV file. """
    try:
        return pd.read_csv(file_path).convert_dtypes()
    except Exception as e:
        logging.error(f"Failed to read table from {file_path}: %s", e)
        raise RuntimeError(f"Failed to read table from {file_path}: %s", e) from e


def main() -> None:
    """ Main function. """
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        df = read_table(file_path)
        summary = prepare_column_summary(df)
        root, _ = os.path.splitext(file_path)
        output_file = f"{root}_summary.json"
        write_dict_to_json(summary, output_file)
    except Exception as e:
        logging.error(f"An error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
