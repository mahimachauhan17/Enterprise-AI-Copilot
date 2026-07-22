/**
 * Sidebar Module
 * 
 * Manages chat history list, document list, sidebar toggle,
 * and mobile responsive behavior.
 */

/**
 * Initialize sidebar functionality.
 */
function initSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const newChatBtn = document.getElementById('newChatBtn');

    // Toggle sidebar
    sidebarToggle.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', closeMobileSidebar);

    // New chat (button may use inline onclick instead)
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }
}

/**
 * Toggle sidebar visibility.
 */
function toggleSidebar() {
    const dashboard = document.getElementById('dashboard');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (window.innerWidth <= 768) {
        // Mobile: slide in/out
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('active');
    } else {
        // Desktop: collapse/expand
        dashboard.classList.toggle('sidebar-collapsed');
    }
}

/**
 * Close mobile sidebar.
 */
function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
}

/**
 * Load chat history from API and render in sidebar.
 */
async function loadChatHistory() {
    try {
        const data = await apiGetHistory();
        if (!data) return;
        renderChatHistory(data.conversations);
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

/**
 * Render chat history list in sidebar.
 */
function renderChatHistory(conversations) {
    const list = document.getElementById('chatHistoryList');

    if (!conversations || conversations.length === 0) {
        list.innerHTML = `
            <div style="padding: 1rem 0.5rem; text-align: center; color: var(--text-tertiary); font-size: 0.8rem;">
                No conversations yet
            </div>
        `;
        return;
    }

    list.innerHTML = conversations.map(conv => `
        <div class="chat-history-item ${conv.id === currentConversationId ? 'active' : ''}" 
             data-id="${conv.id}" 
             onclick="loadConversation(${conv.id})">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span class="chat-history-title">${escapeHtml(conv.title)}</span>
            <button class="chat-history-delete" onclick="event.stopPropagation(); deleteConversation(${conv.id})" title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        </div>
    `).join('');
}

/**
 * Update active conversation highlight in sidebar.
 */
function updateActiveConversation(conversationId) {
    document.querySelectorAll('.chat-history-item').forEach(item => {
        item.classList.toggle('active', parseInt(item.dataset.id) === conversationId);
    });
}

/**
 * Delete a conversation.
 */
async function deleteConversation(conversationId) {
    if (!confirm('Delete this conversation?')) return;

    try {
        await apiDeleteConversation(conversationId);

        // If it's the current conversation, start new chat
        if (conversationId === currentConversationId) {
            startNewChat();
        }

        loadChatHistory();
        showToast('success', 'Deleted', 'Conversation deleted');
    } catch (error) {
        showToast('error', 'Error', 'Failed to delete conversation');
    }
}

/**
 * Load documents list from API and render in sidebar.
 */
async function loadDocuments(search = '') {
    try {
        const data = await apiGetDocuments(search);
        if (!data) return;
        renderDocuments(data.documents);
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

/**
 * Render document list in sidebar.
 */
function renderDocuments(documents) {
    const list = document.getElementById('docList');

    if (!documents || documents.length === 0) {
        list.innerHTML = `
            <div style="padding: 0.75rem 0.5rem; text-align: center; color: var(--text-tertiary); font-size: 0.8rem;">
                No documents uploaded
            </div>
        `;
        return;
    }

    list.innerHTML = documents.map(doc => {
        const iconClass = doc.file_type === 'pdf' ? 'pdf' : doc.file_type === 'docx' ? 'docx' : (doc.file_type === 'csv' || doc.file_type === 'xlsx') ? 'xlsx' : 'txt';
        const statusClass = doc.status;
        const size = formatFileSize(doc.file_size);

        return `
            <div class="doc-item" data-id="${doc.id}">
                <div class="doc-icon ${iconClass}">${doc.file_type.toUpperCase()}</div>
                <div class="doc-info">
                    <div class="doc-name" title="${escapeHtml(doc.original_filename)}">${escapeHtml(doc.original_filename)}</div>
                    <div class="doc-meta">${size} • ${doc.chunk_count} chunks</div>
                </div>
                <div class="doc-status ${statusClass}" title="${doc.status}"></div>
                <button class="doc-delete-btn" onclick="deleteDocument(${doc.id}, '${escapeHtml(doc.original_filename)}')" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
        `;
    }).join('');
}

/**
 * Delete a document.
 */
async function deleteDocument(documentId, filename) {
    if (!confirm(`Delete "${filename}"? This will also remove it from the knowledge base.`)) return;

    try {
        await apiDeleteDocument(documentId);
        loadDocuments();
        showToast('success', 'Deleted', `"${filename}" removed`);
    } catch (error) {
        showToast('error', 'Error', 'Failed to delete document');
    }
}
