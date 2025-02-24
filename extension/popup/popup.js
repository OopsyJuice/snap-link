document.addEventListener('DOMContentLoaded', function() {
    console.log('Extension loaded');
    // Check if we have a token
    chrome.storage.local.get(['authToken'], function(result) {
        if (!result.authToken) {
            showLoginForm();
        } else {
            showURLShortener();
        }
    });
});

function showLoginForm() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h2>SnapLink</h2>
        <div class="login-form">
            <input type="email" id="email" placeholder="Email" class="input-field">
            <input type="password" id="password" placeholder="Password" class="input-field">
            <button id="login">Login</button>
        </div>
        <div id="result"></div>
    `;

    document.getElementById('login').addEventListener('click', handleLogin);
}

async function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const result = document.getElementById('result');

    try {
        const response = await fetch('http://localhost:5001/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();
        if (response.ok) {
            // Store token and show URL shortener
            chrome.storage.local.set({ authToken: data.access_token }, function() {
                showURLShortener();
            });
        } else {
            throw new Error(data.error || 'Login failed');
        }
    } catch (error) {
        result.innerHTML = `
            <div class="error">
                Error: ${error.message}
            </div>
        `;
    }
}

function showURLShortener() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h2>SnapLink</h2>
        <div id="result"></div>
        <button id="shorten">Shorten Current URL</button>
        <button id="logout" class="secondary">Logout</button>
    `;
    
    document.getElementById('shorten').addEventListener('click', handleShorten);
    document.getElementById('logout').addEventListener('click', handleLogout);
}

async function handleShorten() {
    const result = document.getElementById('result');
    const button = document.getElementById('shorten');
    
    try {
        button.disabled = true;
        button.innerHTML = 'Shortening...';

        // Get auth token
        const { authToken } = await chrome.storage.local.get(['authToken']);
        if (!authToken) {
            throw new Error('Please login first');
        }

        // Get current tab URL
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        // Send to our API with auth token
        const response = await fetch('http://localhost:5001/api/shorten', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ url: tab.url })
        });

        const data = await response.json();
        
        if (response.ok) {
            const shortUrl = `http://localhost:5001/${data.short_code}`;
            result.innerHTML = `
                <div class="success">
                    <div class="url-container">
                        <a href="${shortUrl}" target="_blank">${shortUrl}</a>
                        <button class="copy-btn" data-url="${shortUrl}">Copy</button>
                    </div>
                </div>
            `;

            // Add copy functionality
            document.querySelector('.copy-btn').addEventListener('click', async (e) => {
                const url = e.target.dataset.url;
                await navigator.clipboard.writeText(url);
                e.target.innerHTML = 'Copied!';
                setTimeout(() => {
                    e.target.innerHTML = 'Copy';
                }, 2000);
            });
        } else {
            if (response.status === 401) {
                // Token expired or invalid
                chrome.storage.local.remove('authToken');
                showLoginForm();
                throw new Error('Please login again');
            }
            throw new Error(data.error || 'Failed to shorten URL');
        }
    } catch (error) {
        console.error('Error:', error);
        result.innerHTML = `
            <div class="error">
                Error: ${error.message}
            </div>
        `;
    } finally {
        button.disabled = false;
        button.innerHTML = 'Shorten Current URL';
    }
}

function handleLogout() {
    chrome.storage.local.remove('authToken', function() {
        showLoginForm();
    });
}