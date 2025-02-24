document.addEventListener('DOMContentLoaded', function() {
    loadDomains();
    
    const domainForm = document.getElementById('domainForm');
    domainForm.addEventListener('submit', handleDomainSubmit);
});

async function loadDomains() {
    try {
        const response = await fetch('/api/domains');
        const domains = await response.json();
        
        const domainsList = document.querySelector('.domains-list');
        domainsList.innerHTML = domains.map(domain => `
            <div class="domain-item">
                <div class="domain-info">
                    <span class="domain-name">${domain.domain}</span>
                    <span class="domain-status ${domain.verified ? 'verified' : 'pending'}">
                        ${domain.verified ? 'Verified' : 'Pending Verification'}
                    </span>
                </div>
                ${!domain.verified ? `
                    <div class="verification-info">
                        <p>Add this TXT record to verify domain ownership:</p>
                        <code>snaplink-verify=${domain.verification_token}</code>
                        <button class="btn btn-verify" onclick="verifyDomain(${domain.id})">
                            <i class="fas fa-check"></i> Check Verification
                        </button>
                    </div>
                ` : ''}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading domains:', error);
    }
}

async function handleDomainSubmit(e) {
    e.preventDefault();
    
    const input = document.getElementById('domainInput');
    const domain = input.value.trim();
    
    try {
        const response = await fetch('/api/domains', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            input.value = '';
            loadDomains();  // Refresh the domains list
        } else {
            throw new Error(data.error || 'Failed to add domain');
        }
    } catch (error) {
        alert(error.message);
    }
}

async function verifyDomain(domainId) {
    try {
        const response = await fetch(`/api/domains/${domainId}/verify`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            loadDomains();  // Refresh the list
        } else {
            throw new Error(data.error || 'Verification failed');
        }
    } catch (error) {
        alert(error.message);
    }
} 