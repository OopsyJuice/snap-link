document.getElementById('shorten').addEventListener('click', async () => {
    const result = document.getElementById('result');
    const button = document.getElementById('shorten');
    
    try {
      // Show loading state
      button.disabled = true;
      button.innerHTML = 'Shortening...';
      result.innerHTML = '<div class="loading">Creating short link...</div>';
      
      // Get current tab URL
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Send to our API
      const response = await fetch('http://localhost:5001/api/shorten', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: tab.url })
      });
  
      const data = await response.json();
      
      if (response.ok) {
        const shortUrl = `http://localhost:5001/${data.short_code}`;
        result.innerHTML = `
          <div class="success">
            <div class="url-container">
              <a href="${shortUrl}" target="_blank">${shortUrl}</a>
              <button class="copy-btn" data-url="${shortUrl}">
                Copy
              </button>
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
        throw new Error(data.error || 'Failed to shorten URL');
      }
    } catch (error) {
      result.innerHTML = `
        <div class="error">
          Error: ${error.message}
        </div>
      `;
    } finally {
      // Reset button state
      button.disabled = false;
      button.innerHTML = 'Shorten Current URL';
    }
  });