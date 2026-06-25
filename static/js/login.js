// Login Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    const errorMessage = document.getElementById('errorMessage');
    const loginButton = loginForm.querySelector('button[type="submit"]');

    // Toggle password visibility
    togglePassword.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        togglePassword.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // Handle form submission
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset error message
        errorMessage.classList.remove('show');
        errorMessage.textContent = '';
        
        // Disable button
        loginButton.disabled = true;
        loginButton.innerHTML = '<span>Signing in...</span>';
        
        const formData = new FormData(loginForm);
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            // Check if response is OK
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Success - redirect to dashboard
                // Use absolute path or relative path
                const redirectPath = data.redirect || '/dashboard';
                window.location.href = redirectPath;
            } else {
                // Show error
                errorMessage.textContent = data.error || 'Invalid username or password';
                errorMessage.classList.add('show');
                loginButton.disabled = false;
                loginButton.innerHTML = '<span>Sign In</span><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M7.5 15L12.5 10L7.5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
            }
        } catch (error) {
            console.error('Login error:', error);
            errorMessage.textContent = 'An error occurred. Please check your connection and try again.';
            errorMessage.classList.add('show');
            loginButton.disabled = false;
            loginButton.innerHTML = '<span>Sign In</span><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M7.5 15L12.5 10L7.5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        }
    });

    // Add focus animations
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
});

