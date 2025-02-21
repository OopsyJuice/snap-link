document.getElementById('shorten').addEventListener('click', async () => {
    const result = document.getElementById('result');
    
    try {
      // Get current tab URL
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      console.log('Current URL:', tab.url); // Add this for debugging
      
      // Send to our API
      const response = await fetch('http://localhost:5001/api/shorten', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: tab.url })
      });
  
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to shorten URL');
      }
  
      const data = await response.json();
      const shortUrl = `http://localhost:5001/${data.short_code}`;
      result.innerHTML = `
        <div class="success">
          Shortened URL:<br>
          <a href="${shortUrl}" target="_blank">${shortUrl}</a>
        </div>
      `;
    } catch (error) {
      console.error('Error:', error); // Add this for debugging
      result.innerHTML = `
        <div class="error">
          Error: ${error.message}
        </div>
      `;
    }
  });