# Data Analyzer Dashboard

This project provides a web-based dashboard for analyzing CSV data files. It leverages Apache Spark for data processing and Flask for the web application. Users can upload a CSV file, and the application will display an analysis of the dataset, including:

- A dataset overview with column names and types.
- A statistical summary of the dataset.
- A preview of the top 20 rows.
- Summaries of numeric column sums and null value counts.

## Features

- **CSV File Upload**: Users can upload CSV files for analysis.
- **Data Analysis**: The application performs basic data analysis using Apache Spark, including:
  - Descriptive statistics.
  - Conversion of date-like columns to proper date format.
  - Calculation of sums for numeric columns.
  - Null value counting.
- **User-Friendly Interface**: The results are presented in an interactive and well-organized dashboard.
- **Data Preview**: Displays the top 20 rows of the uploaded dataset with formatted values.

## Requirements

- **Python 3.7+**
- **Apache Spark 3.5.3** (or higher)
- **Flask 2.x** (or higher)
- **pyspark** (Apache Spark Python API)
- **Jinja2** (for template rendering)

## Setup

### 1. Install Dependencies

Clone the repository or copy the project files to your local environment. Then, install the required dependencies:

```bash
pip install Flask pyspark
