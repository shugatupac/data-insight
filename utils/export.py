import os
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import tempfile
import uuid
import plotly.io as pio
import logging
import json
from utils.visualizations import generate_visualization

logger = logging.getLogger(__name__)

def export_to_pdf(file_path, fields, visualizations):
    """
    Export analysis results to PDF.
    
    Args:
        file_path (str): Path to the original Excel file
        fields (list): List of fields being analyzed
        visualizations (list): List of visualization configurations
            Each item is a dict with 'field' and 'type' keys
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Generate unique filename
        output_filename = f"analysis_export_{str(uuid.uuid4())[:8]}.pdf"
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Create document elements
        elements = []
        
        # Add title
        elements.append(Paragraph("Excel Data Analysis Report", title_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Add original filename
        original_filename = os.path.basename(file_path)
        elements.append(Paragraph(f"Source file: {original_filename}", normal_style))
        elements.append(Spacer(1, 0.25 * inch))
        
        # Process each field and visualization
        for viz_config in visualizations:
            field = viz_config['field']
            viz_type = viz_config['type']
            
            # Add field heading
            elements.append(Paragraph(f"Analysis of '{field}'", heading_style))
            elements.append(Spacer(1, 0.1 * inch))
            
            # Generate visualization
            viz_data = generate_visualization(file_path, field, viz_type)
            
            # Add visualization based on type
            if viz_type == 'frequency_table':
                elements.append(Paragraph(f"Frequency Table:", styles['Heading3']))
                elements.append(Spacer(1, 0.1 * inch))
                
                # Create table data
                table_data = [['Value', 'Count', 'Percentage (%)']]
                for row in viz_data['data']:
                    table_data.append([
                        str(row['value']), 
                        str(row['count']), 
                        f"{row['percentage']}%"
                    ])
                
                # Create and style the table
                table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            
            else:
                # For charts, create a temporary image and add it
                fig_json = json.dumps(viz_data['data'])
                fig = pio.from_json(fig_json)
                
                # Save as temporary image
                img_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.png")
                try:
                    pio.write_image(fig, img_path, width=600, height=400)
                    
                    # Add image to PDF
                    img = Image(img_path)
                    img.drawWidth = 6 * inch
                    img.drawHeight = 4 * inch
                    elements.append(img)
                    
                    # Clean up
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    logger.error(f"Error adding image to PDF: {str(e)}")
                    elements.append(Paragraph(f"Error rendering {viz_type} visualization: {str(e)}", normal_style))
            
            elements.append(Spacer(1, 0.25 * inch))
        
        # Build the PDF
        doc.build(elements)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting to PDF: {str(e)}")
        raise Exception(f"Error generating PDF export: {str(e)}")

def export_to_excel(file_path, fields, visualizations):
    """
    Export analysis results to Excel.
    
    Args:
        file_path (str): Path to the original Excel file
        fields (list): List of fields being analyzed
        visualizations (list): List of visualization configurations
            Each item is a dict with 'field' and 'type' keys
        
    Returns:
        str: Path to the generated Excel file
    """
    try:
        # Generate unique filename
        output_filename = f"analysis_export_{str(uuid.uuid4())[:8]}.xlsx"
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Read original data
            if file_path.endswith('.csv'):
                original_df = pd.read_csv(file_path)
            else:
                original_df = pd.read_excel(file_path)
            
            # Add original data sheet
            original_df.to_excel(writer, sheet_name='Original Data', index=False)
            
            # Process each visualization
            for viz_config in visualizations:
                field = viz_config['field']
                viz_type = viz_config['type']
                
                # Generate visualization data
                viz_data = generate_visualization(file_path, field, viz_type)
                
                # Create sheet name (combine field and viz type)
                sheet_name = f"{field[:20]}_{viz_type[:10]}"
                
                # For frequency tables, export as a sheet
                if viz_type == 'frequency_table':
                    # Create dataframe from frequency data
                    freq_df = pd.DataFrame(viz_data['data'])
                    freq_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Get workbook and worksheet objects
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]
                    
                    # Add formatting
                    header_format = workbook.add_format({
                        'bold': True,
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    # Write the column headers with the defined format
                    for col_num, value in enumerate(freq_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Adjust column widths
                    worksheet.set_column('A:A', 20)  # Value column
                    worksheet.set_column('B:B', 10)  # Count column
                    worksheet.set_column('C:C', 15)  # Percentage column
                    
                    # Add title
                    title_format = workbook.add_format({
                        'bold': True,
                        'font_size': 14
                    })
                    worksheet.write('A1', f"Frequency Table for {field}", title_format)
                    worksheet.write_row('A2', freq_df.columns, header_format)
                    
                    # Write data starting from row 3
                    for row_num, row_data in enumerate(freq_df.values):
                        worksheet.write_row(row_num + 2, 0, row_data)
                
                # For other visualizations, we can't directly add charts from plotly
                # So we'll create summary sheets with key statistics
                else:
                    # Get the field data
                    if file_path.endswith('.csv'):
                        field_df = pd.read_csv(file_path)
                    else:
                        field_df = pd.read_excel(file_path)
                    
                    # Create summary statistics
                    field_data = field_df[field]
                    
                    # Check if numeric or categorical
                    if pd.api.types.is_numeric_dtype(field_data):
                        # Numeric summary
                        summary_data = {
                            'Statistic': [
                                'Count', 'Mean', 'Median', 'Mode', 
                                'Standard Deviation', 'Minimum', 'Maximum'
                            ],
                            'Value': [
                                field_data.count(),
                                field_data.mean(),
                                field_data.median(),
                                field_data.mode().iloc[0] if not field_data.mode().empty else None,
                                field_data.std(),
                                field_data.min(),
                                field_data.max()
                            ]
                        }
                    else:
                        # Categorical summary (top 10 categories)
                        value_counts = field_data.value_counts().reset_index()
                        value_counts.columns = ['Category', 'Count']
                        value_counts = value_counts.head(10)
                        
                        summary_data = {
                            'Category': value_counts['Category'].tolist(),
                            'Count': value_counts['Count'].tolist(),
                            'Percentage': ((value_counts['Count'] / field_data.count()) * 100).round(2).tolist()
                        }
                    
                    # Create summary dataframe and write to Excel
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Format the worksheet
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]
                    
                    # Add title
                    title_format = workbook.add_format({
                        'bold': True,
                        'font_size': 14
                    })
                    worksheet.write('A1', f"{viz_type.replace('_', ' ').title()} Analysis for {field}", title_format)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        raise Exception(f"Error generating Excel export: {str(e)}")
