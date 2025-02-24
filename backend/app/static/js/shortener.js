document.getElementById('urlForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitButton = document.getElementById('submitButton');
    const originalUrl = document.getElementById('originalUrl').value;
    const domainId = document.getElementById('domainSelect').value;
    const result = document.getElementById('result');

    try {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing';

        const response = await fetch('/api/shorten', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: originalUrl,
                domain_id: domainId || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            const shortUrl = `${data.domain}/${data.short_code}`;
            result.innerHTML = `
                <div class="success">
                    <p>URL shortened successfully!</p>
                    <div class="shortened-url">
                        <span>${shortUrl}</span>
                        <button class="btn-copy" data-url="${shortUrl}">
                            <i class="fas fa-copy"></i>
                        </button>
                    </div>
                </div>
            `;
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
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-link"></i> Shorten';
    }
}); 