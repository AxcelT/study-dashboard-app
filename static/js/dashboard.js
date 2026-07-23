/* Dashboard shell behavior (loaded before Alpine so alpine:init is caught). */

// Root Alpine component: Edit Mode state, persisted across page loads
document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        editMode: localStorage.getItem('editMode') === '1',
        init() {
            this.$watch('editMode', v => localStorage.setItem('editMode', v ? '1' : '0'));
        },
    }));
});

// Course switcher: delegated because the select sits inside #sidebar-live,
// which HTMX re-renders whenever the tree changes
document.addEventListener('change', e => {
    if (e.target.matches('.course-select')) {
        location.href = '/?course=' + e.target.value;
    }
});
