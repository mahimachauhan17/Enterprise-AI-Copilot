/**
 * Chat Module
 * 
 * Handles the chat interface: sending messages, streaming responses,
 * markdown rendering, source citations, and message actions.
 */

let currentConversationId = null;
let isStreaming = false;

/**
 * Send a message and stream the AI response.
 */
async function sendMessage(query) {
    if (!query.trim() || isStreaming) return;

    const settings = getSettings();
    isStreaming = true;

    // Hide empty state and suggestion chips
    const emptyState = document.getElementById('emptyState');
    if (emptyState) emptyState.style.display = 'none';
    const suggestionChips = document.getElementById('suggestionChipsContainer');
    if (suggestionChips) suggestionChips.style.display = 'none';

    // Append user message
    appendMessage('user', query);

    // Clear input
    const input = document.getElementById('chatInput');
    input.value = '';
    input.style.height = 'auto';
    updateSendButton();

    // Show typing indicator
    showTypingIndicator();

    // Create AI message placeholder for streaming
    const aiMsgEl = createStreamingMessage();

    let fullResponse = '';

    await streamChat(
        query,
        currentConversationId,
        {
            temperature: settings.temperature,
            maxTokens: settings.maxTokens,
        },
        // onToken
        (token) => {
            hideTypingIndicator();
            fullResponse += token;
            updateStreamingMessage(aiMsgEl, fullResponse);
        },
        // onDone
        (sources, conversationId, fullResponseFallback) => {
            isStreaming = false;
            hideTypingIndicator();
            const finalContent = fullResponse || fullResponseFallback || '';
            finalizeStreamingMessage(aiMsgEl, finalContent, sources);

            // Update conversation ID
            if (conversationId) {
                currentConversationId = conversationId;
            }

            // Update header title
            const title = query.length > 60 ? query.substring(0, 60) + '...' : query;
            document.getElementById('headerTitle').textContent = title;

            // Refresh chat history in sidebar
            loadChatHistory();
        },
        // onError
        (error) => {
            isStreaming = false;
            hideTypingIndicator();
            aiMsgEl.remove();
            showToast('error', 'Chat Error', error);
        }
    );
}

/**
 * Append a complete message to the chat.
 */
function appendMessage(role, content, sources = null) {
    const messagesEl = document.getElementById('chatMessages');
    const msgEl = document.createElement('div');
    msgEl.className = `message ${role} animate-fade-in-up`;

    const avatarLabel = role === 'user' ? getUserInitials() : 'AI';
    const renderedContent = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);

    msgEl.innerHTML = `
        <div class="message-avatar">${avatarLabel}</div>
        <div class="message-content">
            <div class="message-bubble">${renderedContent}</div>
            ${role === 'assistant' ? createMessageActions(content) : ''}
            ${sources && sources.length ? createSourceCards(sources) : ''}
        </div>
    `;

    messagesEl.appendChild(msgEl);
    highlightCodeBlocks(msgEl);
    scrollToBottom();
}

/**
 * Create a streaming message placeholder.
 */
function createStreamingMessage() {
    const messagesEl = document.getElementById('chatMessages');
    const msgEl = document.createElement('div');
    msgEl.className = 'message assistant animate-fade-in-up';
    msgEl.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-bubble streaming-cursor"></div>
        </div>
    `;
    messagesEl.appendChild(msgEl);
    scrollToBottom();
    return msgEl;
}

/**
 * Update a streaming message with new content.
 */
function updateStreamingMessage(msgEl, content) {
    const bubble = msgEl.querySelector('.message-bubble');
    bubble.innerHTML = renderMarkdown(content);
    bubble.classList.add('streaming-cursor');
    highlightCodeBlocks(msgEl);
    scrollToBottom();
}

/**
 * Finalize a streaming message (remove cursor, add actions & sources).
 */
function finalizeStreamingMessage(msgEl, content, sources) {
    const bubble = msgEl.querySelector('.message-bubble');
    bubble.classList.remove('streaming-cursor');
    bubble.innerHTML = renderMarkdown(content);
    highlightCodeBlocks(msgEl);

    const contentEl = msgEl.querySelector('.message-content');

    // Add message actions
    const actionsHTML = createMessageActions(content);
    contentEl.insertAdjacentHTML('beforeend', actionsHTML);

    // Add source citations
    if (sources && sources.length) {
        contentEl.insertAdjacentHTML('beforeend', createSourceCards(sources));
    }

    scrollToBottom();
}

/**
 * Create message action buttons HTML.
 */
function createMessageActions(content) {
    return `
        <div class="message-actions">
            <button class="message-action-btn" onclick="copyResponse(this, ${JSON.stringify(content).replace(/'/g, "&#39;")})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy
            </button>
            <button class="message-action-btn" onclick="regenerateResponse(this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                Regenerate
            </button>
        </div>
    `;
}

/**
 * Create source citation cards HTML.
 */
function createSourceCards(sources) {
    if (!sources || !sources.length) return '';

    const cards = sources.map((source, i) => {
        const score = source.relevance_score ? `<span class="source-badge score">${Math.round(source.relevance_score * 100)}%</span>` : '';
        const page = source.page_number ? `<span class="source-badge page">Page ${source.page_number}</span>` : '';
        const snippet = source.text_snippet || '';

        return `
            <div class="source-card" onclick="this.classList.toggle('expanded')">
                <div class="source-card-header">
                    <div class="source-card-name">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        ${escapeHtml(source.document_name)}
                    </div>
                    <div class="source-card-badges">${page}${score}</div>
                </div>
                <div class="source-card-snippet">${escapeHtml(snippet)}</div>
            </div>
        `;
    }).join('');

    return `<div class="source-citations">${cards}</div>`;
}

/**
 * Render markdown to HTML using marked.js.
 */
function renderMarkdown(text) {
    if (typeof marked === 'undefined') {
        return escapeHtml(text).replace(/\n/g, '<br>');
    }

    // Configure marked
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    return marked.parse(text);
}

/**
 * Apply syntax highlighting to code blocks.
 */
function highlightCodeBlocks(container) {
    if (typeof hljs === 'undefined') return;
    container.querySelectorAll('pre code').forEach(block => {
        hljs.highlightElement(block);

        // Add copy button to code blocks
        const pre = block.parentElement;
        if (!pre.querySelector('.code-copy-btn')) {
            const btn = document.createElement('button');
            btn.className = 'code-copy-btn';
            btn.textContent = 'Copy';
            btn.onclick = () => {
                navigator.clipboard.writeText(block.textContent);
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            };
            pre.style.position = 'relative';
            pre.appendChild(btn);
        }
    });
}

/**
 * Copy response text to clipboard.
 */
function copyResponse(btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        btn.classList.add('copied');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Copied!
        `;
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = originalHTML;
        }, 2000);
    });
}

/**
 * Regenerate the last AI response.
 */
function regenerateResponse(btn) {
    // Find the preceding user message
    const messageEl = btn.closest('.message');
    const messages = document.querySelectorAll('.message');
    const msgArray = Array.from(messages);
    const index = msgArray.indexOf(messageEl);

    // Find the user message before this assistant message
    for (let i = index - 1; i >= 0; i--) {
        if (msgArray[i].classList.contains('user')) {
            const userText = msgArray[i].querySelector('.message-bubble').textContent;
            // Remove the current AI message
            messageEl.remove();
            // Re-send the query
            sendMessage(userText);
            break;
        }
    }
}

/**
 * Show typing indicator.
 */
function showTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.classList.add('active');
    scrollToBottom();
}

/**
 * Hide typing indicator.
 */
function hideTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.classList.remove('active');
}

/**
 * Scroll chat container to bottom.
 */
function scrollToBottom() {
    const container = document.getElementById('chatContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

/**
 * Load a previous conversation.
 */
async function loadConversation(conversationId) {
    try {
        const data = await apiGetConversation(conversationId);
        if (!data) return;

        currentConversationId = data.id;

        // Clear chat
        const messagesEl = document.getElementById('chatMessages');
        messagesEl.innerHTML = '';

        // Hide empty state and suggestion chips
        const emptyState = document.getElementById('emptyState');
        if (emptyState) emptyState.style.display = 'none';
        const suggestionChips = document.getElementById('suggestionChipsContainer');
        if (suggestionChips) suggestionChips.style.display = 'none';

        // Update header
        document.getElementById('headerTitle').textContent = data.title;

        // Render messages
        data.messages.forEach(msg => {
            appendMessage(msg.role, msg.content, msg.sources);
        });

        // Update active state in sidebar
        updateActiveConversation(conversationId);

        // Close mobile sidebar
        closeMobileSidebar();

    } catch (error) {
        showToast('error', 'Error', 'Failed to load conversation');
    }
}

/**
 * Start a new chat.
 */
function startNewChat() {
    currentConversationId = null;

    const messagesEl = document.getElementById('chatMessages');
    messagesEl.innerHTML = `
        <div class="empty-state animate-fade-in-up animate-delay-1" id="emptyState">
            <div class="ai-orb-container">
                <div class="ai-orb-glow"></div>
                <div class="ai-orb"></div>
            </div>
            <h2><span id="greetingText">What can I help you with?</span></h2>
            <h2 style="font-size:1.8rem; margin-top:-0.5rem;">Ready for your <span class="greeting-accent">questions</span></h2>
            <div style="flex-grow: 1; min-height: 2rem;"></div>
        </div>
    `;
    const suggestionChips = document.getElementById('suggestionChipsContainer');
    if (suggestionChips) suggestionChips.style.display = 'flex';

    // Re-attach suggestion chip listeners
    initSuggestionChips();

    document.getElementById('headerTitle').textContent = 'New Chat';
    updateActiveConversation(null);
    closeMobileSidebar();
}

/**
 * Clear current chat and delete from server.
 */
async function clearCurrentChat() {
    if (!currentConversationId) {
        startNewChat();
        return;
    }

    if (!confirm('Delete this conversation?')) return;

    try {
        await apiDeleteConversation(currentConversationId);
        showToast('success', 'Deleted', 'Conversation deleted');
        startNewChat();
        loadChatHistory();
    } catch (error) {
        showToast('error', 'Error', 'Failed to delete conversation');
    }
}

/**
 * Initialize suggestion chip click handlers.
 */
function initSuggestionChips() {
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        if (chip.dataset.hasListener) return;
        chip.dataset.hasListener = 'true';
        chip.addEventListener('click', () => {
            if (chip.id === 'dataAnalyticsBtn') {
                const hasDocs = document.querySelectorAll('#docList .doc-item').length > 0;
                if (!hasDocs) {
                    document.getElementById('uploadModal').classList.add('active');
                } else {
                    document.getElementById('chatInput').focus();
                }
                return;
            }
            if (chip.id === 'datasetSummaryBtn') {
                const hasDocs = document.querySelectorAll('#docList .doc-item').length > 0;
                if (!hasDocs) {
                    document.getElementById('uploadModal').classList.add('active');
                    return;
                }
            }
            const query = chip.getAttribute('data-query');
            if (query) {
                document.getElementById('chatInput').value = query;
                sendMessage(query);
            }
        });
    });
}

/**
 * Get user initials for avatar.
 */
function getUserInitials() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const name = user.username || 'U';
    return name.charAt(0).toUpperCase();
}

/**
 * Update the send button state based on input.
 */
function updateSendButton() {
    const input = document.getElementById('chatInput');
    const btn = document.getElementById('sendBtn');
    if (btn) {
        btn.disabled = !input.value.trim() || isStreaming;
    }
}

/**
 * Escape HTML characters.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Initialize chat input handlers.
 */
function initChat() {
    const input = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearChatBtn');

    // Auto-resize textarea
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        updateSendButton();
    });

    // Send on Enter (Shift+Enter for new line)
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });

    // Send button click
    sendBtn.addEventListener('click', () => sendMessage(input.value));

    // Clear chat button
    clearBtn.addEventListener('click', clearCurrentChat);

    // Suggestion chips
    initSuggestionChips();
}
