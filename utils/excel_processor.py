import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def validate_excel_file(file_path):
    """
    Validate that the uploaded file is a valid Excel file with data.
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        dict: Validation result with 'valid' and 'message' keys
    """
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Check if the file has data
        if df.empty:
            return {
                'valid': False,
                'message': 'The uploaded file does not contain any data.'
            }
        
        # File is valid
        return {
            'valid': True,
            'message': 'File is valid'
        }
        
    except Exception as e:
        logger.error(f"Error validating file: {str(e)}")
        return {
            'valid': False,
            'message': f'Error reading file: {str(e)}'
        }

def process_excel(file_path, preview_rows=10, filters=None):
    """
    Process an Excel file to extract data for preview with optional filtering.
    
    Args:
        file_path (str): Path to the Excel file
        preview_rows (int): Number of rows to return for preview
        filters (dict, optional): Dictionary of filters to apply {column: value}
        
    Returns:
        tuple: (preview_data, columns) where preview_data is a list of dictionaries
              representing rows, and columns is a list of column names
    """
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Get columns
        columns = df.columns.tolist()
        
        # Apply filters if provided
        if filters and isinstance(filters, dict):
            for column, filter_value in filters.items():
                if column in df.columns:
                    if isinstance(filter_value, dict):
                        # Handle range filters
                        if 'min' in filter_value and pd.api.types.is_numeric_dtype(df[column]):
                            df = df[df[column] >= filter_value['min']]
                        if 'max' in filter_value and pd.api.types.is_numeric_dtype(df[column]):
                            df = df[df[column] <= filter_value['max']]
                        if 'contains' in filter_value:
                            df = df[df[column].astype(str).str.contains(filter_value['contains'], case=False, na=False)]
                    else:
                        # Simple equality filter
                        df = df[df[column].astype(str) == str(filter_value)]
        
        # Convert to list of dictionaries for preview (limit rows)
        preview_data = df.head(preview_rows).replace({np.nan: None}).to_dict('records')
        
        return preview_data, columns, len(df)
    
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise Exception(f"Error processing Excel file: {str(e)}")

def get_column_types(file_path):
    """
    Analyze column types to determine which fields are suitable for analysis.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Dictionary mapping column names to their types
    """
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        column_types = {}
        
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                column_types[column] = 'numeric'
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                column_types[column] = 'datetime'
            elif pd.api.types.is_categorical_dtype(df[column]) or df[column].nunique() < 20:
                column_types[column] = 'categorical'
            else:
                column_types[column] = 'text'
        
        return column_types
    
    except Exception as e:
        logger.error(f"Error getting column types: {str(e)}")
        raise Exception(f"Error analyzing column types: {str(e)}")

def get_field_data(file_path, field):
    """
    Extract data for a specific field from the Excel file.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field/column name to extract
        
    Returns:
        pandas.Series: Data for the specified field
    """
    try:
        # Determine file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        if field not in df.columns:
            raise ValueError(f"Field '{field}' not found in the data")
        
        return df[field]
    
    except Exception as e:
        logger.error(f"Error getting field data: {str(e)}")
        raise Exception(f"Error extracting field data: {str(e)}")

def get_frequency_table(file_path, field):
    """
    Generate a frequency table for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to analyze
        
    Returns:
        dict: Dictionary with value counts and percentages
    """
    try:
        # Get the field data
        field_data = get_field_data(file_path, field)
        
        # Generate value counts
        value_counts = field_data.value_counts().reset_index()
        value_counts.columns = ['value', 'count']
        
        # Calculate percentages
        total = value_counts['count'].sum()
        value_counts['percentage'] = (value_counts['count'] / total * 100).round(2)
        
        # Convert to dictionary
        result = value_counts.to_dict('records')
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating frequency table: {str(e)}")
        raise Exception(f"Error generating frequency table: {str(e)}")
