/**
 * Search Module
 * 
 * Debounced document search by filename.
 */

let searchDebounceTimer = null;

/**
 * Initialize search functionality.
 */
function initSearch() {
    const searchInput = document.getElementById('docSearch');

    searchInput.addEventListener('input', () => {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            const query = searchInput.value.trim();
            loadDocuments(query);
        }, 300);
    });
}
