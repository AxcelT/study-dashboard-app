# Sprint 2: Dynamic UI & Inline Management Overhaul

## Sprint Objective
Transition the Study Dashboard from a static layout into a dynamic, single-page application (SPA) experience. This sprint focuses on reducing friction between reading and managing content by introducing inline editing, seamless deletions, and rapid content creation directly from the main dashboard view, eliminating the need to switch between structural tabs.

## Technology Stack Updates
To achieve a highly responsive interface without rewriting the core backend architecture, the following lightweight frontend tools will be integrated into the existing Flask templates:
*   **HTMX:** To handle asynchronous database requests and inject HTML fragments (inline edits, deletions, form submissions) without full page reloads.
*   **Alpine.js:** To manage local UI state (dropdowns, modals, toggles) purely on the client side without complex vanilla JavaScript files.

---

## Epic 1: Navigation and Hierarchy
**Goal:** Improve visibility of the study structure while keeping the sidebar clean and organized.
*   **Task 1.1:** Refactor the sidebar navigation in `index.html` to utilize Alpine.js (`x-data`, `x-show`, `x-on:click`).
*   **Task 1.2:** Implement collapsible dropdowns for Modules, revealing nested Articles and Sub-articles only when clicked.
*   **Task 1.3:** Ensure active states and parent-child relationships are visually distinct so the user knows exactly where they are in the hierarchy.

## Epic 2: Edit-As-You-Read & Quick Deletion
**Goal:** Allow immediate text and structure manipulation directly from the reading pane and dashboard.
*   **Task 2.1:** Implement an "Edit Mode" toggle switch using Alpine.js within the main reading view.
*   **Task 2.2:** Add inline edit icons to hierarchy titles (Courses, Modules, Articles). Clicking these will trigger an HTMX `hx-get` request to fetch an editable input field from `app.py`.
*   **Task 2.3:** Implement HTMX `hx-put` requests to save edits on "Enter", swapping the updated text back into the DOM seamlessly.
*   **Task 2.4:** Add quick delete (trash) icons next to elements. Use HTMX `hx-delete` with a built-in `hx-confirm` prompt to safely remove records and instantly clear them from the UI.

## Epic 3: Streamlined Content Creation
**Goal:** Bring structural creation tools directly to the primary dashboard.
*   **Task 3.1:** Add a persistent global action button ("+") on the dashboard for adding top-level Courses and Modules.
*   **Task 3.2:** Implement contextual "Add Article" and "Add Sub-article" buttons directly beneath expanded modules in the sidebar tree.
*   **Task 3.3:** Use Alpine.js to trigger centralized modal overlays for content creation forms, rather than forcing navigation to a separate `manage.html` page.
*   **Task 3.4:** Configure HTMX to submit these modal forms in the background and automatically append the newly created items to the existing DOM lists.

## Epic 4: Rich Media Integration
**Goal:** Enhance the core reading and note-taking experience with external assets.
*   **Task 4.1:** Integrate an "Attach Media" button in the article viewing/editing pane.
*   **Task 4.2:** Create an HTMX-powered upload route in `app.py` to handle file uploads or link parsing in the background.
*   **Task 4.3:** Ensure uploaded media (images) or embedded links (videos) render seamlessly within the article flow.

---

## Backend Adjustments (Flask / `app.py`)
To support the HTMX frontend, the Python backend must be updated to serve granular HTML fragments in addition to full page templates.
*   **Task 5.1:** Create modular Jinja templates (e.g., `_edit_form.html`, `_article_row.html`) to serve as targeted responses.
*   **Task 5.2:** Update routing logic in `app.py` to detect HTMX requests by checking for the `HX-Request` header. If present, return only the specific HTML snippet required; if missing, render the full page.

## Acceptance Criteria
- [ ] Sidebar hierarchy collapses and expands smoothly without page reloads.
- [ ] Users can edit titles and article content inline, directly on the dashboard.
- [ ] Users can delete items with a confirmation prompt, instantly removing them from the screen.
- [ ] New items (Courses, Modules, Articles) can be created via modal overlays that update the live view upon submission.
- [ ] Media can be attached to articles and viewed alongside the text.