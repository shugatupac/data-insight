import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import json
import base64
from io import BytesIO
import logging
from utils.excel_processor import get_field_data, get_frequency_table

logger = logging.getLogger(__name__)

def generate_visualization(file_path, field, visualization_type):
    """
    Generate visualization for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to visualize
        visualization_type (str): Type of visualization (frequency_table, pie_chart, bar_chart, treemap)
        
    Returns:
        dict: Visualization data that can be rendered by the frontend
    """
    try:
        # Process data based on visualization type
        if visualization_type == 'frequency_table':
            return generate_frequency_table(file_path, field)
        elif visualization_type == 'pie_chart':
            return generate_pie_chart(file_path, field)
        elif visualization_type == 'bar_chart':
            return generate_bar_chart(file_path, field)
        elif visualization_type == 'treemap':
            return generate_treemap(file_path, field)
        else:
            raise ValueError(f"Unsupported visualization type: {visualization_type}")
    
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise Exception(f"Error generating visualization: {str(e)}")

def generate_frequency_table(file_path, field):
    """
    Generate a frequency table for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to analyze
        
    Returns:
        dict: Frequency table data
    """
    try:
        frequency_data = get_frequency_table(file_path, field)
        
        return {
            'type': 'frequency_table',
            'field': field,
            'data': frequency_data
        }
    
    except Exception as e:
        logger.error(f"Error generating frequency table visualization: {str(e)}")
        raise Exception(f"Error generating frequency table: {str(e)}")

def generate_pie_chart(file_path, field):
    """
    Generate a pie chart visualization for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to visualize
        
    Returns:
        dict: Pie chart data
    """
    try:
        # Get frequency data
        frequency_data = get_frequency_table(file_path, field)
        
        # Limit the number of slices to 10 most frequent, group others
        if len(frequency_data) > 10:
            top_items = sorted(frequency_data, key=lambda x: x['count'], reverse=True)[:9]
            other_items = sorted(frequency_data, key=lambda x: x['count'], reverse=True)[9:]
            other_count = sum(item['count'] for item in other_items)
            other_percentage = sum(item['percentage'] for item in other_items)
            
            top_items.append({
                'value': 'Others',
                'count': other_count,
                'percentage': other_percentage
            })
            
            frequency_data = top_items
        
        # Create pie chart with plotly
        labels = [str(item['value']) for item in frequency_data]
        values = [item['count'] for item in frequency_data]
        
        fig = px.pie(
            names=labels,
            values=values,
            title=f'Distribution of {field}',
            template='plotly_dark'
        )
        
        # Update layout for better appearance
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", y=-0.1),
            font=dict(size=12)
        )
        
        # Convert to JSON for frontend
        chart_json = pio.to_json(fig)
        
        return {
            'type': 'pie_chart',
            'field': field,
            'data': json.loads(chart_json)
        }
    
    except Exception as e:
        logger.error(f"Error generating pie chart: {str(e)}")
        raise Exception(f"Error generating pie chart: {str(e)}")

def generate_bar_chart(file_path, field):
    """
    Generate a bar chart visualization for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to visualize
        
    Returns:
        dict: Bar chart data
    """
    try:
        # Get frequency data
        frequency_data = get_frequency_table(file_path, field)
        
        # Limit the number of bars to 20 most frequent, group others
        if len(frequency_data) > 20:
            top_items = sorted(frequency_data, key=lambda x: x['count'], reverse=True)[:19]
            other_items = sorted(frequency_data, key=lambda x: x['count'], reverse=True)[19:]
            other_count = sum(item['count'] for item in other_items)
            other_percentage = sum(item['percentage'] for item in other_items)
            
            top_items.append({
                'value': 'Others',
                'count': other_count,
                'percentage': other_percentage
            })
            
            frequency_data = top_items
        
        # Sort by count
        frequency_data = sorted(frequency_data, key=lambda x: x['count'])
        
        # Create bar chart with plotly
        x_values = [str(item['value']) for item in frequency_data]
        y_values = [item['count'] for item in frequency_data]
        
        fig = px.bar(
            x=y_values,
            y=x_values,
            orientation='h',
            title=f'Distribution of {field}',
            labels={'x': 'Count', 'y': field},
            template='plotly_dark'
        )
        
        # Update layout for better appearance
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12)
        )
        
        # Convert to JSON for frontend
        chart_json = pio.to_json(fig)
        
        return {
            'type': 'bar_chart',
            'field': field,
            'data': json.loads(chart_json)
        }
    
    except Exception as e:
        logger.error(f"Error generating bar chart: {str(e)}")
        raise Exception(f"Error generating bar chart: {str(e)}")

def generate_treemap(file_path, field):
    """
    Generate a treemap visualization for a field.
    
    Args:
        file_path (str): Path to the Excel file
        field (str): Field to visualize
        
    Returns:
        dict: Treemap data
    """
    try:
        # Get frequency data
        frequency_data = get_frequency_table(file_path, field)
        
        # Create a DataFrame for the treemap
        df = pd.DataFrame(frequency_data)
        
        # Add a text column that combines value and count for better display
        df['display_text'] = df['value'].astype(str) + '<br>Count: ' + df['count'].astype(str)
        
        # Create treemap with plotly
        fig = px.treemap(
            df,
            path=[pd.Series(['Root'] * len(df)), 'display_text'],
            values='count',
            title=f'Treemap of {field}',
            template='plotly_dark',
            hover_data=['value', 'count', 'percentage'],
            color='count',  # Add coloring based on count
            color_continuous_scale='RdBu'
        )
        
        # Update layout for better appearance
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12)
        )
        
        # Convert to JSON for frontend
        chart_json = pio.to_json(fig)
        
        return {
            'type': 'treemap',
            'field': field,
            'data': json.loads(chart_json)
        }
    
    except Exception as e:
        logger.error(f"Error generating treemap: {str(e)}")
        raise Exception(f"Error generating treemap: {str(e)}")

def get_plot_image(fig, format='png', width=800, height=600):
    """
    Convert a plotly figure to a base64 encoded image.
    
    Args:
        fig: Plotly figure object
        format (str): Image format (png, jpeg, etc.)
        width (int): Image width in pixels
        height (int): Image height in pixels
        
    Returns:
        str: Base64 encoded image
    """
    try:
        img_bytes = pio.to_image(fig, format=format, width=width, height=height)
        encoded = base64.b64encode(img_bytes).decode('ascii')
        return f"data:image/{format};base64,{encoded}"
    
    except Exception as e:
        logger.error(f"Error converting plot to image: {str(e)}")
        raise Exception(f"Error generating image: {str(e)}")
