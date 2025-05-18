import os
import logging
from flask import Flask, render_template, request, jsonify, url_for, flash, redirect, session, send_file
from werkzeug.utils import secure_filename
import uuid
import pandas as pd
import json
import tempfile
from utils.excel_processor import process_excel, get_column_types, validate_excel_file
from utils.visualizations import generate_visualization
from utils.export import export_to_pdf, export_to_excel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Limit file size to 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
# Configure uploads folder in temp directory
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate unique ID for this session
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        
        # Secure filename and save
        filename = secure_filename(file.filename or "")  # Provide default empty string if None
        if not filename:
            flash('Invalid filename', 'error')
            return redirect(url_for('index'))
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(file_path)
        session['uploaded_file_path'] = file_path
        
        try:
            # Validate the file
            validation_result = validate_excel_file(file_path)
            if not validation_result['valid']:
                flash(validation_result['message'], 'error')
                return redirect(url_for('index'))
            
            # Process the Excel file to get preview data
            preview_data, columns = process_excel(file_path, preview_rows=10)
            column_types = get_column_types(file_path)
            
            # Store data in session
            session['preview_data'] = json.dumps(preview_data)
            session['columns'] = columns
            session['column_types'] = column_types
            
            # Return success with data
            return render_template('index.html', 
                                  preview_data=preview_data,
                                  columns=columns,
                                  column_types=column_types,
                                  filename=filename)
        
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            flash(f"Error processing file: {str(e)}", 'error')
            return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload .xlsx, .xls, or .csv files.', 'error')
        return redirect(url_for('index'))

@app.route('/analyze', methods=['POST', 'GET'])
def analyze():
    if request.method == 'GET':
        # For GET requests, just render the analysis page
        return redirect(url_for('index'))
        
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        
        field = data.get('field')
        visualization_types = data.get('visualization_types', [])
        
        logger.debug(f"Field: {field}, Visualization Types: {visualization_types}")
        
        if not field or not visualization_types:
            logger.error("Field or visualization types missing")
            return jsonify({'error': 'Field and visualization types are required'}), 400
        
        # Get the file path from session
        file_path = session.get('uploaded_file_path')
        logger.debug(f"File path from session: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({'error': 'No file uploaded or file not found'}), 400
        
        # Generate visualizations
        results = {}
        for viz_type in visualization_types:
            try:
                logger.debug(f"Generating {viz_type} visualization for field: {field}")
                viz_data = generate_visualization(file_path, field, viz_type)
                results[viz_type] = viz_data
                logger.debug(f"Successfully generated {viz_type}")
            except Exception as e:
                logger.error(f"Error generating {viz_type} visualization: {str(e)}")
                logger.exception("Full traceback:")
                results[viz_type] = {'error': str(e)}
        
        logger.debug(f"Returning results for {len(results)} visualizations")
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Error in analyze: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST', 'GET'])
def export():
    if request.method == 'GET':
        # For GET requests, just redirect to the index
        return redirect(url_for('index'))
        
    try:
        data = request.get_json()
        logger.debug(f"Export request data: {data}")
        
        export_type = data.get('export_type')
        fields = data.get('fields', [])
        visualizations = data.get('visualizations', [])
        
        if not export_type or not fields or not visualizations:
            logger.error("Missing required export parameters")
            return jsonify({'error': 'Export type, fields, and visualizations are required'}), 400
        
        # Get the file path from session
        file_path = session.get('uploaded_file_path')
        logger.debug(f"Export using file path: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found for export: {file_path}")
            return jsonify({'error': 'No file uploaded or file not found'}), 400
        
        # Export based on selected type
        if export_type == 'pdf':
            logger.debug("Exporting to PDF")
            output_path = export_to_pdf(file_path, fields, visualizations)
        elif export_type == 'excel':
            logger.debug("Exporting to Excel")
            output_path = export_to_excel(file_path, fields, visualizations)
        else:
            logger.error(f"Invalid export type: {export_type}")
            return jsonify({'error': 'Invalid export type'}), 400
        
        # Generate a download URL
        download_url = url_for('download_file', filename=os.path.basename(output_path), _external=True)
        logger.debug(f"Generated download URL: {download_url}")
        return jsonify({'download_url': download_url})
    
    except Exception as e:
        logger.error(f"Error in export: {str(e)}")
        logger.exception("Full export error traceback:")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    session_id = session.get('session_id')
    if not session_id:
        flash('Session expired', 'error')
        return redirect(url_for('index'))
    
    # Path to the exported file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    # Return the file for download
    return send_file(file_path, as_attachment=True)

# We will handle file cleanup explicitly instead of on every request
# to prevent premature deletion of files needed for analysis
@app.teardown_appcontext
def cleanup_files(error):
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
