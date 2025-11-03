from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import uuid
from werkzeug.utils import secure_filename

from ResumeParser import process_resume

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "resume-parser"}), 200

@app.route('/api/process', methods=['POST'])
def api_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4().hex
        saved_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(saved_pdf)

        json_out = f"resume_result_{unique_id}.json"
        csv_out = f"resume_result_{unique_id}.csv"
        try:
            result = process_resume(saved_pdf, json_filename=json_out, csv_filename=csv_out)
            downloads = {
                'json': f"/download/{json_out}",
                'csv': f"/download/{csv_out}"
            }
            return jsonify({'result': result, 'downloads': downloads})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(BASE_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=False, port=5000)
