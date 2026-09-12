# MIS505-DataWrangling
Course Projects and Projects Based on Them

The tables in this repository all have the same format, each containing the same data for different countries.

The format, in JSON in the TableDescriptor.json file, is as follows (This display does not format JSON properly):

{
    "tableName": "Assignment8_Argentina",
    "_tableName_comment": "The name of the year sequence table in this country's database.",
    "_columns_comment": "An array of objects, each representing a column.",
    "columns": [
        {
            "name": "Year",
            "description": "The year for which the particular data was gathered.",
            "dataType": "INTEGER",
            "constraints": {
                "primaryKey": false,
                "autoIncrement": false,
                "notNull": true
            }
        },
        {
            "name": "Primary Enrollment",
            "description": "The total number of students enrolled in primary education in the country during the subject year.",
            "dataType": "NUMERIC",
            "constraints": {
                "notNull": false
            },
            "_comment": "The data source downloaded is not guaranteed to be complete so there can be missing values."
        },
        {
            "name": "GDP",
            "description": "The Gross Domestic Product of the country in U.S. Dollars in the subject year.",
            "dataType": "NUMERIC",
            "constraints": {
                "notNull": false
            },
            "_comment": "The data source downloaded is not guaranteed to be complete so there can be missing values."
        },
    ]
}
