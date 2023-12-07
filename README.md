# Data Dictionary Generation
## Overview
This project provides a suite of tools for creating an AI-assisted data dictionary.
It's primarily for educational use and focuses on simplicity and adaptability. 

There are three distinct components:
1. **Summary Statistics Generation:**
Generate summary statistics for each column in a database table.
2. **Base Table Description Creation:**
Construct a basic description of the table.
3. **Table Description Update:**
Update the basic table description using the summary statistics.

## Key Features
**Modularity:**
Each component is designed to be independent, allowing for easy updates, replacements, and testing.

**Scalability Considerations:**
While this implementation uses Pandas for statistics generation, it is designed for easy replacement of the summary statistics component.
The summary statistics should run directly in the data warehouse for scalability.

**OpenAI Integration:**
The project leverages OpenAI's capabilities to enhance table and column descriptions.

## Components
### Summary Statistics Generation (generate_summary_statistics.py)
This script is isolated for ease of modification. It currently uses Pandas, but direct database querying is recommended for large-scale applications.
There is minimal downstream impact if the JSON schema is altered.

### Base Table Description (create_data_dictionary_stub.py)
This script reads a CSV file's header and creates a crude JSON-formatted data dictionary as a placeholder.
It then interacts with the OpenAI Table Describer assistant, which modifies the JSON values while keeping the keys constant.
The updates are based table and column names and any additional information saved in the prompt.
It requires local_util.py

### Table Description Update (complete_data_dictionary.py)
The final component integrates the outputs of the first two scripts, enriching the column descriptions with detailed summary statistics.
It interacts with the OpenAI Column Describer assistant, which modifies the JSON values while keeping the keys constant.
It requires local_util.py

## Usage
### Environment Setup
* Use a Python virtual environment (e.g., Conda with Python 3.10).
* Install required libraries
* Execute each script (generate_summary_statistics.py, create_data_dictionary_stub.py, complete_data_dictionary.py).

### Create summary statistics for each column in a table
generate_summary_statistics.py is isolated to allow easy replacement with something database-specific.
Gathering column statistics via Pandas is not scalable.
At scale, it's best to use the database or data warehouse itself to gather these statistics.
A sample can be downloaded to CSV to test the code and improve prompts.

This program does not interact with OpenAI.
The JSON format is as follows:
```
{
    "Numeric_Example": {
        "column_name": "Numeric_Example",
        "data_type": "numeric",
        "unique_values_count": 10,
        "missing_values_count": 1,
        "sample_entries": [10, 20, 30, 40, 50],
        "summary_statistics": {
            "mean": 30,
            "median": 30,
            "std": 15,
            "min": 10,
            "max": 50
        },
        "deciles": {
            "10%": 10,
            "20%": 20,
            "30%": 30,
            "40%": 40,
            "50%": 50,
            "60%": 60,
            "70%": 70,
            "80%": 80,
            "90%": 90
        }
    },
    "Text_Example": {
        "column_name": "Text_Example",
        "data_type": "string",
        "unique_values_count": 5,
        "missing_values_count": 0,
        "sample_entries": ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"],
        "top_n_values": {
            "Text 1": 5,
            "Text 2": 4,
            "Text 3": 3,
            "Text 4": 2,
            "Text 5": 1
        }
    }
}
```
### Create a base table table description
create_data_dictionary_stub.py is a program that reads the header row of a CSV file and constructs a placeholder data dictionary in JSON format.
It first creates a stub with the table and column names.
It then passes this stub to the OpenAI Table Describer assistant.
The assistant alters the JSON values but leaves the keys unchanged.


This is partitioned so the table description is separate from the column description.
In toy examples, this portion adds little value; however, in a real case, the Table Describer prompt should be heavily modified for the specifics of the overall database.
Reference to how tables join to other tables would go in the Table Describer prompt. In addition, the purpose of the warehouse and main use cases of the data could be inserted.

This program interacts with OpenAI and imports local_util.py. 
The JSON format is as follows:
```
{
    "Table Name": "Table_Name",
    "Table Description": "The table description goes here.",
    "Columns": [
        {
            "Column Name": "Column_01",
            "Column Description": "Description of the first column goes here.",
            "Column Data Notes": "Notes for column go here."
        }, ... 
```
## Update table description based on summary statistics
complete_data_dictionary.py consumes the output from create_data_dictionary_stub.py and generate_summary_statistics.py.
It updates the output of create_data_dictionary_stub.py using the information from generate_summary_statistics.py.
The output JSON has the exact keys as the create_data_dictionary_stub.py output, only the values are different.

This is partitioned for two reasons.
* First, the Column Describer prompt takes in more column-specific information than the Table Describer.
It, therefore, should have its own prompt to assist its more detailed output and require less general database information.
* Second, this code may require refactoring based on scale.
For large tables, OpenAI may have difficulty consuming two large JSON files.
In that case, it may be required to chunk the summary data by column and loop through. Making an OpenAI COLUMN Describer call at each iteration.

This program interacts with OpenAI and imports local_util.py.

## Prompts
The prompts can be created with code. 
In general, I don't recommend this approach.
Getting prompts correct requires a lot of trial and error, particularly when narrowing down a specific use case.
This code is divided for ease of OpenAI playground iteration.

Included are the general prompt language I used, but they can be greatly improved for specific use cases.

### Create Table Describer Prompt
Table_Describer_prompt.txt contains the prompt for a first draft of a data dictionary.
It's based on a common sense guess from the names of the table and fields.
More should be added to include the business use case for the data in the schema.
Join information across tables could also be added here.

### Create Column Describer Prompt
Column_Describer_prompt.txt contains the prompt used to update the data dictionary using summary statistics per column. For tables with a modest number of columns, it should work.
However, the code and prompt require modification for tables with large numbers of columns.
The code could chunk requests on a per-column basis. 
The prompt could be adjusted to accept per column request and ensure it does not alter columns unrelated to the specified column.

## Example using program
### Create a new Python environment
There are many Python virtual environments to choose from. I used conda with Python 3.10.

Install the Python requirements.

`pip install -r requirements.txt`

generate_summary_statistics.py does not require environment variables.

### Run generate_summary_statistics.py
`python generate_summary_statistics.py employee.csv`

In this example, employee_summary.json should now exist in the example directory.

### Set .env variables
Both create_data_dictionary_stub.py and complete_data_dictionary.py call OpenAI assistants.
For this, the environment variables must be set.
```
# Set the key for the OpenAI API
OPENAI_API_KEY=

# Set the Assistant ID for the Table Describer
TABLE_DESCRIBER=

# Set the Assistant ID for the Column Describer
COLUMN_SUBSCRIBER=
```

### Run create_data_dictionary_stub.py
`python create_data_dictionary_stub.py employee.csv`

After this, employee_base.json exists in the example table.

### Run complete_data_dictionary.py
Given the output from the other two programs, we can now create the data dictionary.

`python complete_data_dictionary.py employee_base.json example/employee_data_dictionary.json`

The output to this is employee_data_dictionary.json. The final data dictionary.

The design of this process allows for easy debugging of the prompt. 
In the OpenAI playground, the Column Describer can be tested by pasting in the JSON values.
Many prompt versions can be tested without rerunning any code.
