from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Dynamically set BASE_DIR to the 'notes' folder inside your project directory
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'notes')

def get_directory_tree():
    """Scans the BASE_DIR and returns a nested dictionary of certificates, courses, and modules."""
    tree = {}
    
    # If the base directory doesn't exist yet, return an empty tree
    if not os.path.exists(BASE_DIR):
        return tree
        
    for cert in os.listdir(BASE_DIR):
        cert_path = os.path.join(BASE_DIR, cert)
        
        # Only look at directories (this correctly ignores your .md files in the root)
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
        # Retrieve directory structure inputs
        certificate = request.form.get('certificate').strip()
        course = request.form.get('course').strip()
        module = request.form.get('module').strip()
        
        # Retrieve content inputs
        content_type = request.form.get('content_type')
        title = request.form.get('title')
        content = request.form.get('content')

        # Ensure the module filename ends with .txt
        if not module.endswith('.txt'):
            module += '.txt'

        # Build paths and create directories if they do not exist
        dir_path = os.path.join(BASE_DIR, certificate, course)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, module)

        # Append to the targeted text file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write("\n===\n")
            if content_type == 'video':
                f.write(f"Sub-Article: {title} (Video)\n")
                f.write("Video Transcript:\n")
            elif content_type == 'reading':
                f.write(f"Sub-Article: {title} (Reading)\n")
            f.write(f"{content}\n")

        return redirect(url_for('index'))

    # On GET request, fetch the directory tree and pass it to the template
    dir_tree = get_directory_tree()
    return render_template('index.html', dir_tree=dir_tree)

if __name__ == '__main__':
    app.run(debug=True)