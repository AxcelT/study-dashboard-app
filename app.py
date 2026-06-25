from flask import Flask, render_template, request, redirect, url_for
import os
import logging
from logging.handlers import RotatingFileHandler

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
    """Scans the BASE_DIR and returns a nested dictionary of certificates, courses, and modules."""
    tree = {}
    
    # If the base directory doesn't exist yet, return an empty tree
    if not os.path.exists(BASE_DIR):
        return tree
        
    for cert in os.listdir(BASE_DIR):
        cert_path = os.path.join(BASE_DIR, cert)
        
        # Only look at directories
        if os.path.isdir(cert_path):
            tree[cert] = {}
            for course in os.listdir(cert_path):
                course_path = os.path.join(cert_path, course)
                
                # Only process course directories
                if os.path.isdir(course_path):
                    tree[cert][course] = []
                    # Scan for text files inside the course folder
                    for file in os.listdir(course_path):
                        if file.endswith('.txt'):
                            tree[cert][course].append(file)
                    
    return tree

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.info("--- New Form Submission ---")
        
        # Retrieve directory structure inputs
        certificate = request.form.get('certificate').strip()
        course = request.form.get('course').strip()
        module = request.form.get('module').strip()
        
        # Retrieve content inputs
        content_type = request.form.get('content_type')
        title = request.form.get('title')
        content = request.form.get('content')

        # Logging Stuff
        logger.debug(f"Received Route Data -> Cert: '{certificate}', Course: '{course}', Module: '{module}'")
        logger.debug(f"Received Content Data -> Type: '{content_type}', Title: '{title}'")
        logger.debug(f"Content Length -> {len(content) if content else 0} characters")

        # Ensure the module filename ends with .txt
        if not module.endswith('.txt'):
            module += '.txt'

        # Build paths and create directories if they do not exist
        dir_path = os.path.join(BASE_DIR, certificate, course)
        
        try:
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, module)
            logger.debug(f"File path resolved to: {file_path}")

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write("\n===\n")
                if content_type == 'video':
                    logger.debug("Executing branch: content_type == 'video'")
                    f.write(f"Sub-Article: {title} (Video)\n")
                    f.write("Video Transcript:\n")

                elif content_type == 'reading':
                    logger.debug("Executing branch: content_type == 'reading'")
                    f.write(f"Sub-Article: {title} (Reading)\n")

                else:
                    logger.warning(f"Unmatched content_type: '{content_type}'. Neither 'video' nor 'reading' logic executed.")
                
                f.write(f"{content}\n")
            
            logger.info("Successfully wrote content to file.")
            
        except Exception as e:
            # LOGGER: If the script fails to write to the file due to permissions or missing directories
            logger.error(f"Failed to write to file due to error: {e}", exc_info=True)

        return redirect(url_for('index'))

    # On GET request, fetch the directory tree and pass it to the template
    dir_tree = get_directory_tree()
    return render_template('index.html', dir_tree=dir_tree)

if __name__ == '__main__':
    app.run(debug=True)