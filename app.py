
from flask import Flask, render_template, request, redirect, url_for, abort, flash, make_response
from werkzeug.utils import secure_filename, safe_join
from markdown import markdown
import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
import re

app = Flask(__name__)
app.secret_key = 'dev-only-secret-key'  # required for flash messages; replace before any deployment

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

# --- Notes Hierarchy ---
# notes/<course>/<xx_module>/<xx_article>/<xx_subarticle>.md      raw pasted content
# notes/<course>/<xx_module>/<xx_article>/<xx_subarticle>.ai.md   AI compiled artifact
#
# Courses are certificates (not numbered). Modules, articles, and sub-articles
# carry an xx_ numeric prefix so alphabetical sort gives the course sequence.
AI_SUFFIX = '.ai.md'
AI_PLACEHOLDER = "AI Compiled Reading Artifact will go here."

# Path components must be plain slugs — blocks traversal and junk names.
SLUG_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_\-]*$')


def slugify(name):
    return re.sub(r'[^A-Za-z0-9]+', '_', name.strip()).strip('_').lower()


def display_name(slug):
    """'02_networking_fundamentals' -> 'Networking Fundamentals'"""
    return re.sub(r'^\d+_', '', slug).replace('_', ' ').title()


def seq_prefix(entry):
    m = re.match(r'^(\d+)_', entry)
    return m.group(1) if m else None


def next_prefix(parent_dir):
    """Next zero-padded sequence number among numbered entries in parent_dir."""
    highest = 0
    if os.path.isdir(parent_dir):
        for entry in os.listdir(parent_dir):
            m = re.match(r'^(\d+)_', entry)
            if m:
                highest = max(highest, int(m.group(1)))
    return f"{highest + 1:02d}"


def scan_notes():
    """Walk the notes tree into course -> modules -> articles -> sub_articles."""
    courses = []
    if not os.path.isdir(BASE_DIR):
        return courses

    for course in sorted(os.listdir(BASE_DIR)):
        course_path = os.path.join(BASE_DIR, course)
        if not os.path.isdir(course_path):
            continue

        modules = []
        for module in sorted(os.listdir(course_path)):
            module_path = os.path.join(course_path, module)
            if not os.path.isdir(module_path):
                continue

            articles = []
            for article in sorted(os.listdir(module_path)):
                article_path = os.path.join(module_path, article)
                if not os.path.isdir(article_path) or article == 'media':
                    continue

                subs = []
                for entry in sorted(os.listdir(article_path)):
                    if entry.endswith(AI_SUFFIX) or not entry.endswith('.md'):
                        continue
                    stem = entry[:-3]
                    subs.append({
                        'slug': stem,
                        'title': display_name(stem),
                        'has_ai': os.path.isfile(os.path.join(article_path, stem + AI_SUFFIX)),
                    })
                articles.append({'slug': article, 'title': display_name(article), 'sub_articles': subs})
            modules.append({'slug': module, 'title': display_name(module), 'articles': articles})
        courses.append({'slug': course, 'title': display_name(course), 'modules': modules})
    return courses


def resolve_child(parent_dir, typed_name, numbered=True):
    """Map a user-typed name onto an existing child dir/file-stem, or mint a
    new numbered slug. Matches exact names first, then names ignoring the
    xx_ prefix, so 'networking_fundamentals' finds '02_networking_fundamentals'."""
    slug = slugify(typed_name)
    if not slug:
        return None
    if os.path.isdir(parent_dir):
        for entry in sorted(os.listdir(parent_dir)):
            if entry == typed_name or entry == slug:
                return entry
            if re.sub(r'^\d+_', '', entry) == slug:
                return entry
    if not numbered:
        return slug
    return f"{next_prefix(parent_dir)}_{slug}"


# --- Dashboard Routes ---

@app.route('/')
def index():
    courses = scan_notes()
    selected = request.args.get('course')
    current_course = next((c for c in courses if c['slug'] == selected),
                          courses[0] if courses else None)
    return render_template('index.html', courses=courses, current_course=current_course,
                           active=None, sub_title=None, raw_content=None, artifact_html=None)


@app.route('/view/<course>/<module>/<article>/<sub>')
def view_sub_article(course, module, article, sub):
    for part in (course, module, article, sub):
        if not SLUG_RE.match(part):
            abort(404)

    article_dir = safe_join(BASE_DIR, course, module, article)
    if article_dir is None or not os.path.isdir(article_dir):
        abort(404)

    raw_path = os.path.join(article_dir, sub + '.md')
    if not os.path.isfile(raw_path):
        logger.warning(f"Sub-article not found: {course}/{module}/{article}/{sub}")
        abort(404)

    with open(raw_path, encoding='utf-8') as f:
        raw_content = f.read()

    ai_path = os.path.join(article_dir, sub + AI_SUFFIX)
    if os.path.isfile(ai_path):
        with open(ai_path, encoding='utf-8') as f:
            ai_text = f.read()
    else:
        ai_text = AI_PLACEHOLDER

    artifact_html = markdown(ai_text, extensions=['tables', 'fenced_code'])

    courses = scan_notes()
    current_course = next((c for c in courses if c['slug'] == course), None)
    active = {'course': course, 'module': module, 'article': article, 'sub': sub}
    return render_template('index.html', courses=courses, current_course=current_course,
                           active=active, sub_title=display_name(sub),
                           crumb_module=display_name(module), crumb_article=display_name(article),
                           raw_content=raw_content, artifact_html=artifact_html)


# --- Structure Management (adjust courses / modules / articles) ---

@app.route('/manage')
def manage():
    return render_template('manage.html', courses=scan_notes())


@app.route('/manage/create', methods=['POST'])
def manage_create():
    kind = request.form.get('kind', '')
    name = request.form.get('name', '')
    slug = slugify(name)
    if not slug:
        flash(('error', 'Name cannot be empty.'))
        return redirect(url_for('manage'))

    try:
        if kind == 'course':
            target = safe_join(BASE_DIR, slug)
        elif kind == 'module':
            course = request.form.get('course', '')
            parent = safe_join(BASE_DIR, course)
            if parent is None or not os.path.isdir(parent):
                raise ValueError('Pick a valid course.')
            target = os.path.join(parent, f"{next_prefix(parent)}_{slug}")
        elif kind == 'article':
            course, module = request.form.get('parent', '').split('/', 1)
            parent = safe_join(BASE_DIR, course, module)
            if parent is None or not os.path.isdir(parent):
                raise ValueError('Pick a valid module.')
            target = os.path.join(parent, f"{next_prefix(parent)}_{slug}")
        else:
            raise ValueError('Unknown item type.')

        if target is None:
            raise ValueError('Invalid name.')
        if os.path.exists(target):
            raise ValueError(f"'{os.path.basename(target)}' already exists.")

        os.makedirs(target)
        logger.info(f"Created {kind}: {target}")
        flash(('success', f"Created {kind} '{os.path.basename(target)}'."))
    except ValueError as e:
        flash(('error', str(e)))
    except OSError as e:
        logger.error(f"Failed to create {kind}: {e}", exc_info=True)
        flash(('error', f"Could not create {kind}: {e}"))
    return redirect(url_for('manage'))


@app.route('/manage/rename', methods=['POST'])
def manage_rename():
    rel_path = request.form.get('path', '')
    new_name = request.form.get('name', '')
    new_pos = request.form.get('position', '').strip()

    parts = rel_path.split('/')
    if not all(SLUG_RE.match(p) for p in parts):
        flash(('error', 'Invalid target path.'))
        return redirect(url_for('manage'))

    abs_path = safe_join(BASE_DIR, *parts)
    if abs_path is None or not os.path.isdir(abs_path):
        flash(('error', 'Target no longer exists.'))
        return redirect(url_for('manage'))

    old_base = os.path.basename(abs_path)
    slug = slugify(new_name) or re.sub(r'^\d+_', '', old_base)

    if len(parts) == 1:
        # Courses carry no sequence number
        new_base = slug
    else:
        if new_pos:
            if not new_pos.isdigit():
                flash(('error', 'Position must be a number.'))
                return redirect(url_for('manage'))
            prefix = f"{int(new_pos):02d}"
        else:
            prefix = seq_prefix(old_base) or next_prefix(os.path.dirname(abs_path))
        new_base = f"{prefix}_{slug}"

    if new_base == old_base:
        flash(('success', 'Nothing to change.'))
        return redirect(url_for('manage'))

    new_path = os.path.join(os.path.dirname(abs_path), new_base)
    if os.path.exists(new_path):
        flash(('error', f"'{new_base}' already exists."))
        return redirect(url_for('manage'))

    try:
        os.rename(abs_path, new_path)
        logger.info(f"Renamed {abs_path} -> {new_path}")
        flash(('success', f"Renamed '{old_base}' to '{new_base}'."))
    except OSError as e:
        logger.error(f"Rename failed: {e}", exc_info=True)
        flash(('error', f"Rename failed: {e}"))
    return redirect(url_for('manage'))


# --- Inline Node Editing (HTMX fragment routes) ---
# A "node" rel_path identifies one tree entry:
#   <course>                       directory
#   <course>/<module>              directory
#   <course>/<module>/<article>    directory
#   <course>/<module>/<article>/<sub_stem>   .md / .ai.md file pair
# Responses are HTML fragments swapped into the sidebar by HTMX. Mutations set
# 'HX-Trigger: tree-changed' so the whole sidebar re-renders with fresh paths.

def parse_node(rel_path):
    """Validate a node rel_path and confirm it exists on disk. Returns parts or None."""
    parts = rel_path.split('/')
    if not 1 <= len(parts) <= 4 or not all(SLUG_RE.match(p) for p in parts):
        return None
    if len(parts) <= 3:
        abs_dir = safe_join(BASE_DIR, *parts)
        if abs_dir is None or not os.path.isdir(abs_dir):
            return None
    else:
        article_dir = safe_join(BASE_DIR, *parts[:3])
        if article_dir is None or not os.path.isfile(os.path.join(article_dir, parts[3] + '.md')):
            return None
    return parts


def node_title_context(parts):
    ctx = {'rel_path': '/'.join(parts), 'title': display_name(parts[-1]), 'is_active': False}
    if len(parts) == 4:
        article_dir = safe_join(BASE_DIR, *parts[:3])
        ctx['has_ai'] = os.path.isfile(os.path.join(article_dir, parts[3] + AI_SUFFIX))
    return ctx


@app.route('/sidebar')
def sidebar():
    """Sidebar header + tree fragment, refetched whenever tree-changed fires."""
    courses = scan_notes()
    selected = request.args.get('course')
    current_course = next((c for c in courses if c['slug'] == selected),
                          courses[0] if courses else None)
    active = None
    if current_course and request.args.get('sub'):
        active = {'course': current_course['slug'], 'module': request.args.get('module'),
                  'article': request.args.get('article'), 'sub': request.args.get('sub')}
    return render_template('partials/_sidebar.html', courses=courses,
                           current_course=current_course, active=active)


@app.route('/node/title/<path:rel_path>')
def node_title(rel_path):
    """Plain title fragment — used to cancel an inline edit."""
    parts = parse_node(rel_path)
    if parts is None:
        abort(404)
    return render_template('partials/_node_title.html', **node_title_context(parts))


@app.route('/node/edit/<path:rel_path>')
def node_edit(rel_path):
    """Inline rename form fragment, swapped in place of the title."""
    parts = parse_node(rel_path)
    if parts is None:
        abort(404)
    return render_template('partials/_edit_form.html', rel_path=rel_path,
                           current_name=display_name(parts[-1]))


@app.route('/node/rename/<path:rel_path>', methods=['PUT'])
def node_rename(rel_path):
    parts = parse_node(rel_path)
    if parts is None:
        abort(404)

    typed = request.form.get('name', '')
    slug = slugify(typed)

    def edit_form(error):
        return render_template('partials/_edit_form.html', rel_path=rel_path,
                               current_name=typed or display_name(parts[-1]), error=error)

    if not slug:
        return edit_form('Name cannot be empty.')

    old_base = parts[-1]
    if len(parts) == 1:
        new_base = slug          # courses carry no sequence number
    else:
        parent_dir = safe_join(BASE_DIR, *parts[:-1])
        prefix = seq_prefix(old_base) or next_prefix(parent_dir)
        new_base = f"{prefix}_{slug}"

    if new_base == old_base:
        return render_template('partials/_node_title.html', **node_title_context(parts))

    try:
        if len(parts) <= 3:
            abs_path = safe_join(BASE_DIR, *parts)
            new_path = os.path.join(os.path.dirname(abs_path), new_base)
            if os.path.exists(new_path):
                return edit_form(f"'{new_base}' already exists.")
            os.rename(abs_path, new_path)
        else:
            article_dir = safe_join(BASE_DIR, *parts[:3])
            new_raw = os.path.join(article_dir, new_base + '.md')
            if os.path.exists(new_raw):
                return edit_form(f"'{new_base}' already exists.")
            os.rename(os.path.join(article_dir, old_base + '.md'), new_raw)
            old_ai = os.path.join(article_dir, old_base + AI_SUFFIX)
            if os.path.isfile(old_ai):
                os.rename(old_ai, os.path.join(article_dir, new_base + AI_SUFFIX))
    except OSError as e:
        logger.error(f"Inline rename failed for {rel_path}: {e}", exc_info=True)
        return edit_form(f"Rename failed: {e}")

    new_parts = parts[:-1] + [new_base]
    logger.info(f"Renamed node {rel_path} -> {'/'.join(new_parts)}")
    resp = make_response(render_template('partials/_node_title.html',
                                         **node_title_context(new_parts)))
    resp.headers['HX-Trigger'] = 'tree-changed'
    return resp


@app.route('/node/delete/<path:rel_path>', methods=['DELETE'])
def node_delete(rel_path):
    parts = parse_node(rel_path)
    if parts is None:
        abort(404)

    try:
        if len(parts) <= 3:
            shutil.rmtree(safe_join(BASE_DIR, *parts))
        else:
            article_dir = safe_join(BASE_DIR, *parts[:3])
            stem = parts[3]
            os.remove(os.path.join(article_dir, stem + '.md'))
            ai_path = os.path.join(article_dir, stem + AI_SUFFIX)
            if os.path.isfile(ai_path):
                os.remove(ai_path)
            # Media files uploaded for this sub-article follow the <stem>_<idx>.<ext> scheme
            media_dir = os.path.join(article_dir, 'media')
            if os.path.isdir(media_dir):
                media_re = re.compile(rf'^{re.escape(stem)}_\d+\.')
                for entry in os.listdir(media_dir):
                    if media_re.match(entry):
                        os.remove(os.path.join(media_dir, entry))
    except OSError as e:
        logger.error(f"Inline delete failed for {rel_path}: {e}", exc_info=True)
        return f"Delete failed: {e}", 500

    logger.info(f"Deleted node {rel_path}")
    resp = make_response('', 200)
    resp.headers['HX-Trigger'] = 'tree-changed'
    return resp


# --- Notes Compiler (adds sub-article content into the hierarchy) ---

@app.route('/compiler', methods=['GET', 'POST'])
def compiler():
    if request.method == 'POST':
        logger.info("--- New Compiler Submission ---")

        course = slugify(request.form.get('course', ''))
        module_name = request.form.get('module', '').strip()
        article_name = request.form.get('article', '').strip()
        content_type = request.form.get('content_type')
        title = request.form.get('title', '').strip()
        # We don't strip content yet so we preserve newlines around placeholders
        content = request.form.get('content', '')

        try:
            if not (course and module_name and article_name and title):
                raise ValueError('All routing fields are required.')

            course_dir = safe_join(BASE_DIR, course)
            if course_dir is None:
                raise ValueError('Invalid course name.')
            module_slug = resolve_child(course_dir, module_name)
            article_slug = resolve_child(os.path.join(course_dir, module_slug), article_name) if module_slug else None
            if not module_slug or not article_slug:
                raise ValueError('Invalid module/article name.')

            article_dir = os.path.join(course_dir, module_slug, article_slug)
            os.makedirs(article_dir, exist_ok=True)

            # Sub-article file pair: <xx_name>.md (raw) + <xx_name>.ai.md (artifact)
            # Match an existing sub-article ignoring its xx_ prefix, else mint a new stem
            existing = None
            sub_slug = slugify(title)
            for entry in sorted(os.listdir(article_dir)):
                if entry.endswith('.md') and not entry.endswith(AI_SUFFIX):
                    if re.sub(r'^\d+_', '', entry[:-3]) == sub_slug:
                        existing = entry[:-3]
                        break
            sub_stem = existing or f"{next_prefix(article_dir)}_{sub_slug}"
            raw_path = os.path.join(article_dir, sub_stem + '.md')
            ai_path = os.path.join(article_dir, sub_stem + AI_SUFFIX)

            uploaded_files = request.files.getlist('media')

            # 1. PROCESS MULTIPLE MEDIA FILES & INJECT INTO CONTENT
            if uploaded_files and uploaded_files[0].filename != '':
                media_dir = os.path.join(article_dir, 'media')
                os.makedirs(media_dir, exist_ok=True)

                for idx, file in enumerate(uploaded_files):
                    if file and file.filename:
                        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
                        new_filename = secure_filename(f"{sub_stem}_{idx}.{ext}")
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

            # 2. WRITE THE RAW SUB-ARTICLE FILE
            is_new = not os.path.exists(raw_path)
            with open(raw_path, 'a', encoding='utf-8') as f:
                if is_new:
                    f.write(f"# {title} ({content_type.capitalize()})\n\n")
                else:
                    f.write("\n\n---\n\n")
                f.write(f"{content.strip()}\n")

            # 3. SEED THE AI ARTIFACT PLACEHOLDER (never overwrite a real artifact)
            if not os.path.exists(ai_path):
                with open(ai_path, 'w', encoding='utf-8') as f:
                    f.write(AI_PLACEHOLDER + "\n")

            logger.info(f"Compiled sub-article: {raw_path}")
            flash(('success', f"Saved to {course}/{module_slug}/{article_slug}/{sub_stem}.md"))

        except ValueError as e:
            flash(('error', str(e)))
        except Exception as e:
            logger.error(f"Failed to write to file due to error: {e}", exc_info=True)
            flash(('error', f"Failed to save: {e}"))

        return redirect(url_for('compiler'))

    return render_template('compiler.html', courses=scan_notes())


if __name__ == '__main__':
    app.run(debug=True)
