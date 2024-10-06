import os
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import pandas as pd
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from fpdf import FPDF

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
REPORT_FOLDER = 'reports'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

# Ensure upload and report directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected for uploading.'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'status': 'success', 'message': 'File uploaded successfully.', 'filename': filename})
    else:
        return jsonify({'status': 'error', 'message': 'Allowed file types are CSV and XLSX.'}), 400


@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    data = request.get_json()
    chart_type = data.get('type')
    filename = data.get('filename')

    if not chart_type or not filename:
        return jsonify({'status': 'error', 'message': 'Chart type and filename are required.'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        return jsonify({'status': 'error', 'message': 'Uploaded file not found.'}), 404

    # Read data
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error reading the file: {str(e)}'}), 500

    # Check if there are at least two columns
    if df.shape[1] < 2:
        return jsonify({'status': 'error', 'message': 'The uploaded file must have at least two columns.'}), 400

    # Determine chart parameters based on chart type
    try:
        if chart_type == 'bar':
            # Example: Bar chart for Q1 Sales
            x = df['Category']
            y = df['Sales_Q1']
            plt.bar(x, y, color='skyblue')
            plt.xlabel('Category')
            plt.ylabel('Sales Q1')
            plt.title('Bar Chart - Q1 Sales')
            # Add data labels
            for i, value in enumerate(y):
                plt.text(i, value + (max(y) * 0.01), f'{value}', ha='center')
        
        elif chart_type == 'pie':
            # Example: Pie chart for Total Sales
            df['Total_Sales'] = df[['Sales_Q1', 'Sales_Q2', 'Sales_Q3', 'Sales_Q4']].sum(axis=1)
            x = df['Category']
            y = df['Total_Sales']
            plt.pie(y, labels=x, autopct='%1.1f%%', startangle=140)
            plt.title('Pie Chart - Total Sales')
        
        elif chart_type == 'line':
            # Example: Line chart for Sales Trends
            quarters = ['Sales_Q1', 'Sales_Q2', 'Sales_Q3', 'Sales_Q4']
            plt.figure(figsize=(10, 6))
            for index, row in df.iterrows():
                plt.plot(quarters, row[quarters], marker='o', label=row['Category'])
                # Add data labels
                for q, sales in zip(quarters, row[quarters]):
                    plt.text(q, sales, f'{sales}', fontsize=9, ha='center', va='bottom')
            plt.xlabel('Quarter')
            plt.ylabel('Sales')
            plt.title('Line Chart - Sales Trends')
            plt.legend(title='Category')
        
        else:
            return jsonify({'status': 'error', 'message': 'Invalid chart type specified.'}), 400

        # Save the chart as an image
        chart_filename = f"{chart_type}_chart_{filename.rsplit('.',1)[0]}.png"
        chart_path = os.path.join(app.config['UPLOAD_FOLDER'], chart_filename)
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

        # Return the URL to the generated chart
        chart_url = url_for('static', filename=f'uploads/{chart_filename}')
        return jsonify({'status': 'success', 'chart_url': chart_url, 'chart_filename': chart_filename})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error generating the chart: {str(e)}'}), 500


@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()
    filename = data.get('filename')
    charts = data.get('charts')  # List of chart URLs

    if not filename or not charts:
        return jsonify({'status': 'error', 'message': 'Filename and charts are required to generate report.'}), 400

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Data Visualization Report", ln=True, align='C')

    # Filename
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Source File: {filename}", ln=True, align='L')

    for chart_url in charts:
        chart_path = chart_url.replace('/static/', '')
        full_chart_path = os.path.join('static', chart_path)
        if os.path.exists(full_chart_path):
            pdf.ln(10)
            try:
                pdf.image(full_chart_path, w=180)
            except Exception as e:
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Error adding image: {chart_path}", ln=True, align='L')
        else:
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Chart not found: {chart_path}", ln=True, align='L')

    report_filename = f"report_{filename.rsplit('.',1)[0]}.pdf"
    report_path = os.path.join(app.config['REPORT_FOLDER'], report_filename)
    try:
        pdf.output(report_path)
        report_url = url_for('download_report', filename=report_filename)
        return jsonify({'status': 'success', 'report_url': report_url})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error generating report: {str(e)}'}), 500

@app.route('/download_report/<filename>', methods=['GET'])
def download_report(filename):
    return send_from_directory(REPORT_FOLDER, filename, as_attachment=True)

@app.route('/clear', methods=['POST'])
def clear():
    try:
        # Clear uploaded files
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Clear reports
        for filename in os.listdir(REPORT_FOLDER):
            file_path = os.path.join(REPORT_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return jsonify({'status': 'success', 'message': 'All files and reports have been cleared.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error clearing files: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)


