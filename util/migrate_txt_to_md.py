import os

# Set this to the path of your notes directory
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'notes')

def migrate_txt_to_md():
    if not os.path.exists(BASE_DIR):
        print(f"Directory not found: {BASE_DIR}")
        return

    # Walk through all directories and files in the notes folder
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.txt'):
                txt_filepath = os.path.join(root, file)
                
                # Read the old .txt file
                with open(txt_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Split the document by the old delimiter
                # Note: Handles both === with and without newlines gracefully
                chunks = [chunk.strip() for chunk in content.split('===') if chunk.strip()]
                
                md_content = ""
                
                for chunk in chunks:
                    # 1. Handle top-level Module or Article declarations
                    if chunk.startswith('Module ') or chunk.startswith('Article:'):
                        md_content += f"# {chunk}\n\n"
                        continue
                        
                    # 2. Handle Sub-Articles (The main content)
                    if chunk.startswith('Sub-Article:'):
                        lines = chunk.split('\n')
                        
                        # The first line is the Title (e.g., "Sub-Article: Module 1 Introduction (Video)")
                        title_line = lines[0].strip()
                        md_content += f"## {title_line}\n\n"
                        
                        content_start_index = 1
                        
                        # Check if the second line is "Video Transcript:"
                        if len(lines) > 1 and lines[1].strip() == 'Video Transcript:':
                            md_content += "### Video Transcript:\n\n"
                            content_start_index = 2
                        
                        # Append the rest of the text content
                        if len(lines) > content_start_index:
                            body_text = '\n'.join(lines[content_start_index:]).strip()
                            md_content += f"{body_text}\n\n"
                    else:
                        # Fallback for any orphaned text
                        md_content += f"{chunk}\n\n"

                # Create the new .md filename
                md_filepath = txt_filepath.replace('.txt', '.md')
                
                # Write to the new .md file
                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                print(f"Successfully migrated: {file} -> {os.path.basename(md_filepath)}")
                
                # OPTIONAL: Uncomment the line below to delete the old .txt files automatically
                # os.remove(txt_filepath)

if __name__ == '__main__':
    print("Starting migration...")
    migrate_txt_to_md()
    print("Migration complete!")