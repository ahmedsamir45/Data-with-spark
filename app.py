import os
import tempfile
from flask import Flask, request, render_template
from pyspark.sql import SparkSession
from pyspark.sql.types import NumericType, DateType, TimestampType
import pyspark.sql.functions as F
from pyspark.sql.functions import format_number, col, to_date, date_format

app = Flask(__name__)
# /home/ahmed/miniconda3/bin/python "/home/ahmed/Desktop/Data with spark/app.py"

# Initialize Spark session
os.environ['SPARK_HOME'] = '/home/ubuntu/spark-3.5.3-bin-hadoop3'
os.environ['PATH'] += os.pathsep + os.path.join(os.environ['SPARK_HOME'], 'bin')
spark = SparkSession.builder.appName("DataAnalyzer").getOrCreate()

def format_value(value, column_type):
    """Format values based on their type."""
    if value is None:
        return "null"
    if isinstance(column_type, (DateType, TimestampType)):
        return value.strftime("%Y-%m-%d") if hasattr(value, 'strftime') else str(value)
    if isinstance(column_type, NumericType):
        try:
            return format_number(value, 2)
        except:
            return str(value)
    return str(value)

@app.route('/')
def index():
    """Render the main page with upload form."""
    return render_template('index.html', data=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and perform data analysis."""
    temp_file = None
    try:
        # Retrieve file
        file = request.files['file']
        if not file:
            raise ValueError("No file was uploaded.")

        # Save the file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)

        # Read the dataset with date inference
        df = spark.read.csv(temp_file.name, header=True, inferSchema=True)

        # Try to convert string columns that look like dates
        for column in df.columns:
            # Check if column might contain dates
            sample = df.select(column).limit(10).collect()
            if any(isinstance(row[0], str) for row in sample):
                try:
                    # Try multiple date formats
                    for date_format in ["yyyy-MM-dd", "MM/dd/yyyy", "dd-MM-yyyy", "yyyy/MM/dd"]:
                        df = df.withColumn(
                            f"{column}_temp",
                            to_date(col(column), date_format)
                        )
                        # If successful conversion, replace original column
                        if not df.filter(col(f"{column}_temp").isNotNull()).limit(1).rdd.isEmpty():
                            df = df.drop(column).withColumnRenamed(f"{column}_temp", column)
                            break
                        else:
                            df = df.drop(f"{column}_temp")
                except:
                    continue

        if df.rdd.isEmpty():
            raise ValueError("The uploaded dataset is empty.")

        # Dataset columns
        columns = df.columns
        
        # Get schema information
        schema_info = {field.name: field.dataType for field in df.schema.fields}

        # Get description DataFrame
        desc_df = df.describe()
        
        # Format numerical columns
        formatted_desc = desc_df.select(
            [col("summary")] + 
            [format_number(col(c).cast('float'), 2).alias(c) 
             for c in desc_df.columns if c != "summary" and 
             isinstance(schema_info[c], NumericType)]
        )
        
        # Convert to list of lists for template rendering
        description = [
            [row["summary"]] + [row[c] if c in row else "N/A" for c in columns]
            for row in formatted_desc.collect()
        ]

        # Top 20 rows with proper date formatting
        top_20_df = df.limit(20)
        top_20_rows = []
        for row in top_20_df.collect():
            formatted_row = {}
            for column in columns:
                value = row[column]
                formatted_row[column] = format_value(value, schema_info[column])
            top_20_rows.append(formatted_row)

        # Identify numeric columns
        numeric_columns = [col for col in df.columns if isinstance(schema_info[col], NumericType)]

        # Calculate and format sum of numeric columns
        sum_df = df.select([F.sum(F.col(col)).alias(col) for col in numeric_columns])
        formatted_sums = sum_df.select(
            [format_number(col(c).cast('float'), 2).alias(c) for c in numeric_columns]
        ).collect()[0]
        sum_values_dict = {col: formatted_sums[idx] for idx, col in enumerate(numeric_columns)}

        # Count null values for each column
        null_counts = df.select([F.count(F.when(F.col(col).isNull(), col)).alias(col) for col in df.columns]).collect()
        null_counts_dict = {col: null_counts[0][idx] for idx, col in enumerate(df.columns)}

        # Add column type information
        column_types = {col: str(schema_info[col]) for col in columns}

        # Prepare data for rendering
        data = {
            "columns": columns,
            "column_types": column_types,
            "description": description,
            "top_20": top_20_rows,
            "sum": sum_values_dict,
            "null_counts": null_counts_dict
        }

        return render_template('index.html', data=data)

    except ValueError as ve:
        return render_template('index.html', data={"error": str(ve)})
    except Exception as e:
        return render_template('index.html', data={"error": f"An unexpected error occurred: {str(e)}"})
    finally:
        # Clean up the temporary file
        if temp_file:
            os.unlink(temp_file.name)

if __name__ == '__main__':
    app.run(debug=True)