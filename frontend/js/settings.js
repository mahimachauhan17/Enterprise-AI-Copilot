/**
 * Settings Module
 * 
 * Manages temperature, max tokens, LLM model selection,
 * and chat history clearing. Settings persist in localStorage.
 */

const DEFAULT_SETTINGS = {
    temperature: 0.3,
    maxTokens: 2048,
    llmModel: 'llama-3.3-70b-versatile',
};

/**
 * Initialize settings module.
 */
function initSettings() {
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    const settingsModalClose = document.getElementById('settingsModalClose');
    const temperatureSlider = document.getElementById('temperatureSlider');
    const tempValue = document.getElementById('tempValue');
    const maxTokensInput = document.getElementById('maxTokensInput');
    const llmModelSelect = document.getElementById('llmModelSelect');
    const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');

    // Load saved settings
    const settings = getSettings();
    temperatureSlider.value = settings.temperature;
    tempValue.textContent = settings.temperature;
    maxTokensInput.value = settings.maxTokens;
    llmModelSelect.value = settings.llmModel;

    // Open modal
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.classList.add('active');
        });
    }

    // Close modal
    const closeModal = () => settingsModal.classList.remove('active');
    settingsModalClose.addEventListener('click', closeModal);
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeModal();
    });

    // Temperature slider
    temperatureSlider.addEventListener('input', () => {
        const val = parseFloat(temperatureSlider.value).toFixed(1);
        tempValue.textContent = val;
        saveSettings({ temperature: parseFloat(val) });
    });

    // Max tokens
    maxTokensInput.addEventListener('change', () => {
        let val = parseInt(maxTokensInput.value);
        val = Math.max(100, Math.min(8192, val || 2048));
        maxTokensInput.value = val;
        saveSettings({ maxTokens: val });
    });

    // LLM model
    llmModelSelect.addEventListener('change', () => {
        saveSettings({ llmModel: llmModelSelect.value });
        showToast('info', 'Model Updated', `Now using ${llmModelSelect.options[llmModelSelect.selectedIndex].text}`);
    });

    // Clear all history
    clearAllHistoryBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete ALL chat history? This cannot be undone.')) return;

        try {
            await apiClearHistory();
            startNewChat();
            loadChatHistory();
            showToast('success', 'History Cleared', 'All conversations have been deleted');
            closeModal();
        } catch (error) {
            showToast('error', 'Error', 'Failed to clear history');
        }
    });
}

/**
 * Get current settings from localStorage.
 */
function getSettings() {
    try {
        const saved = JSON.parse(localStorage.getItem('settings') || '{}');
        return { ...DEFAULT_SETTINGS, ...saved };
    } catch {
        return { ...DEFAULT_SETTINGS };
    }
}

/**
 * Save settings to localStorage (partial update).
 */
function saveSettings(partial) {
    const current = getSettings();
    const updated = { ...current, ...partial };
    localStorage.setItem('settings', JSON.stringify(updated));
}
