/**
 * Authentication Module
 * 
 * Handles login and signup form submission,
 * JWT storage, and password strength validation.
 */

/**
 * Handle login form submission.
 */
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const btn = document.getElementById('loginBtn');

    // Clear previous errors
    clearFormErrors();

    // Validate
    if (!email) {
        showFormError('emailGroup', 'emailError', 'Email is required');
        return;
    }
    if (!password) {
        showFormError('passwordGroup', 'passwordError', 'Password is required');
        return;
    }

    // Submit
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        const data = await apiLogin(email, password);
        if (data) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = '/dashboard';
        }
    } catch (error) {
        showToast('error', 'Login Failed', error.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

/**
 * Handle signup form submission.
 */
async function handleSignup(e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const btn = document.getElementById('signupBtn');

    // Clear previous errors
    clearFormErrors();

    // Validate
    if (!username || username.length < 3) {
        showFormError('usernameGroup', 'usernameError', 'Username must be at least 3 characters');
        return;
    }
    if (!email) {
        showFormError('emailGroup', 'emailError', 'Email is required');
        return;
    }
    if (!password || password.length < 6) {
        showFormError('passwordGroup', 'passwordError', 'Password must be at least 6 characters');
        return;
    }
    if (password !== confirmPassword) {
        showFormError('confirmPasswordGroup', 'confirmPasswordError', 'Passwords do not match');
        return;
    }

    // Submit
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        const data = await apiSignup(username, email, password);
        if (data) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            showToast('success', 'Account Created', 'Welcome to Enterprise AI Copilot!');
            setTimeout(() => window.location.href = '/dashboard', 1000);
        }
    } catch (error) {
        showToast('error', 'Signup Failed', error.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

/**
 * Show a form field error.
 */
function showFormError(groupId, errorId, message) {
    const group = document.getElementById(groupId);
    const error = document.getElementById(errorId);
    if (group) group.classList.add('error');
    if (error) {
        error.textContent = message;
        error.style.display = 'block';
    }
}

/**
 * Clear all form errors.
 */
function clearFormErrors() {
    document.querySelectorAll('.form-group').forEach(g => g.classList.remove('error'));
    document.querySelectorAll('.form-error').forEach(e => {
        e.textContent = '';
        e.style.display = 'none';
    });
}

/**
 * Update password strength indicator.
 */
function updatePasswordStrength() {
    const password = document.getElementById('password').value;
    const bar = document.getElementById('strengthBar');
    if (!bar) return;

    bar.className = 'password-strength-bar';

    if (password.length === 0) {
        bar.style.width = '0%';
        return;
    }

    let score = 0;
    if (password.length >= 6) score++;
    if (password.length >= 10) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 2) {
        bar.classList.add('weak');
    } else if (score <= 3) {
        bar.classList.add('medium');
    } else {
        bar.classList.add('strong');
    }
}

/**
 * Logout user.
 */
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('settings');
    window.location.href = '/';
}

/**
 * Check if user is authenticated. Redirect to login if not.
 */
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return false;
    }
    return true;
}
