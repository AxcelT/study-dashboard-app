/* Notes Compiler helpers. */

// Fill the routing fields from a click on the structure tree
function autofill(course, module, article) {
    document.getElementById('course').value = course;
    document.getElementById('module').value = module;
    document.getElementById('article').value = article;

    if (module === '') {
        document.getElementById('module').focus();
    } else if (article === '') {
        document.getElementById('article').focus();
    } else {
        document.getElementById('title').focus();
    }
}

//Media Placeholder Logic
let mediaCount = 0;

function insertMediaPlaceholder() {
    const textarea = document.getElementById('content');
    const placeholder = `\n\n[[MEDIA_${mediaCount}]]\n\n`;

    // Find cursor position
    const startPos = textarea.selectionStart;
    const endPos = textarea.selectionEnd;

    // Inject placeholder at cursor
    textarea.value = textarea.value.substring(0, startPos) +
                    placeholder +
                    textarea.value.substring(endPos, textarea.value.length);

    // Move cursor after the inserted placeholder and refocus
    textarea.selectionStart = textarea.selectionEnd = startPos + placeholder.length;
    textarea.focus();

    mediaCount++;
}
