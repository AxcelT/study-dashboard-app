
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import logging
from logging.handlers import RotatingFileHandler
import re

app = Flask(__name__)

# --- Directory Setup ---
# Dynamically set BASE_DIR to the 'notes' folder
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes')
# Dynamically set LOGS_DIR to the 'logs' folder
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')

# Ensure the logs directory exists before setting up the logger
os.makedirs(LOGS_DIR, exist_ok=True)
log_file_path = os.path.join(LOGS_DIR, 'app_debug.log')

# --- Logger Configuration (Volatility Feature) ---
# maxBytes=1048576 limits each file to 1 Megabyte.
# backupCount=2 keeps the active log + 2 historical logs (3 total).
# When app_debug.log hits 1MB, it is renamed to app_debug.log.1, and a new one starts.
file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=2)
stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

def get_directory_tree():
    tree = {}
    if not os.path.exists(BASE_DIR):
        return tree
        
    for cert in os.listdir(BASE_DIR):
        cert_path = os.path.join(BASE_DIR, cert)
        if os.path.isdir(cert_path):
            tree[cert] = {}
            for course in os.listdir(cert_path):
                course_path = os.path.join(cert_path, course)
                if os.path.isdir(course_path):
                    tree[cert][course] = []
                    # Scan for .md files instead of .txt
                    for file in os.listdir(course_path):
                        if file.endswith('.md'):
                            tree[cert][course].append(file)
    return tree

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.info("--- New Form Submission ---")
        
        certificate = request.form.get('certificate').strip()
        course = request.form.get('course').strip()
        module = request.form.get('module').strip()
        
        content_type = request.form.get('content_type')
        title = request.form.get('title')
        # We don't strip content yet so we preserve newlines around placeholders
        content = request.form.get('content') 

        if not module.endswith('.md'):
            module += '.md'

        dir_path = os.path.join(BASE_DIR, certificate, course)
        
        try:
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, module)
            
            uploaded_files = request.files.getlist('media')
            
            # 1. PROCESS MULTIPLE MEDIA FILES & INJECT INTO CONTENT
            if uploaded_files and uploaded_files[0].filename != '':
                media_dir = os.path.join(dir_path, 'media')
                os.makedirs(media_dir, exist_ok=True)
                
                safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title).lower()
                base_module = module.replace('.md', '')
                
                for idx, file in enumerate(uploaded_files):
                    if file and file.filename:
                        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                        new_filename = secure_filename(f"{base_module}_{safe_title}_{idx}.{ext}")
                        media_path = os.path.join(media_dir, new_filename)
                        
                        file.save(media_path)
                        
                        # Generate the Markdown image string
                        markdown_img = f"![Attached Media: {new_filename}](media/{new_filename})"
                        
                        # Look for the specific placeholder in the text
                        placeholder = f"[[MEDIA_{idx}]]"
                        
                        if placeholder in content:
                            # Replace the placeholder with the actual image markdown
                            content = content.replace(placeholder, markdown_img)
                        else:
                            # Fallback: If they forgot the placeholder, append to the bottom
                            content += f"\n\n{markdown_img}"

            # 2. WRITE FINAL MARKDOWN TO FILE
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"\n## Sub-Article: {title} ({content_type.capitalize()})\n\n")
                
                if content_type == 'video':
                    f.write("### Video Transcript:\n")
                
                # Write the content (now containing the inline image links)
                f.write(f"{content.strip()}\n\n")
            
            logger.info("Successfully wrote content and inline media to file.")
            
        except Exception as e:
            logger.error(f"Failed to write to file due to error: {e}", exc_info=True)

        return redirect(url_for('index'))

    dir_tree = get_directory_tree()
    return render_template('index.html', dir_tree=dir_tree)

if __name__ == '__main__':
    app.run(debug=True)