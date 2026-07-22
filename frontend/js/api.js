/**
 * API Client
 * 
 * Centralized API communication layer with JWT authentication,
 * error handling, and SSE streaming support.
 */

const API_BASE = window.location.origin + '/api';

/**
 * Make an authenticated API request.
 * Automatically injects JWT token and handles 401 redirects.
 */
async function apiFetch(url, options = {}) {
    const token = localStorage.getItem('token');
    
    const headers = {
        ...options.headers,
    };

    // Add auth header if token exists (don't add Content-Type for FormData)
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Add JSON content type unless sending FormData
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers,
        });

        // Handle 401 - redirect to login
        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
            return null;
        }

        // Parse response
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || `Request failed with status ${response.status}`);
        }

        return data;
    } catch (error) {
        if (error.message === 'Failed to fetch') {
            showToast('error', 'Connection Error', 'Unable to connect to the server.');
        }
        throw error;
    }
}

/**
 * Stream chat response via SSE using fetch + ReadableStream.
 * 
 * @param {string} query - User's question
 * @param {number|null} conversationId - Existing conversation ID
 * @param {object} settings - Temperature, max_tokens overrides
 * @param {function} onToken - Callback for each streamed token
 * @param {function} onDone - Callback when streaming completes with sources
 * @param {function} onError - Callback on error
 */
async function streamChat(query, conversationId, settings, onToken, onDone, onError) {
    const token = localStorage.getItem('token');
    
    const body = {
        query,
        stream: true,
        ...(conversationId && { conversation_id: conversationId }),
        ...(settings.temperature !== undefined && { temperature: settings.temperature }),
        ...(settings.maxTokens !== undefined && { max_tokens: settings.maxTokens }),
    };

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(body),
        });

        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
            return;
        }

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Chat request failed');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE events
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'token') {
                            onToken(data.content);
                        } else if (data.type === 'done') {
                            onDone(data.sources || [], data.conversation_id, data.full_response);
                        } else if (data.type === 'error') {
                            onError(data.content);
                        }
                    } catch (e) {
                        // Skip malformed JSON
                    }
                }
            }
        }
    } catch (error) {
        onError(error.message);
    }
}

// --- API Helper Methods ---

async function apiLogin(email, password) {
    return apiFetch('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
}

async function apiSignup(username, email, password) {
    return apiFetch('/signup', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
    });
}

async function apiGetDocuments(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return apiFetch(`/documents${query}`);
}

async function apiDeleteDocument(documentId) {
    return apiFetch(`/document/${documentId}`, { method: 'DELETE' });
}

async function apiGetHistory() {
    return apiFetch('/history');
}

async function apiGetConversation(conversationId) {
    return apiFetch(`/history/${conversationId}`);
}

async function apiDeleteConversation(conversationId) {
    return apiFetch(`/history/${conversationId}`, { method: 'DELETE' });
}

async function apiClearHistory() {
    return apiFetch('/history', { method: 'DELETE' });
}

// --- Toast Notification System ---

function showToast(type, title, message, duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-message">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="this.closest('.toast').remove()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
    `;

    container.appendChild(toast);

    // Auto-remove
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
