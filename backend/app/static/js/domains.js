// Domain management and verification
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('verificationModal');
    const closeBtn = modal.querySelector('.close');
    const addDomainBtn = document.getElementById('addDomain');
    const domainInput = document.getElementById('domainInput');

    // Close modal when clicking the X
    closeBtn.onclick = () => modal.style.display = 'none';

    // Close modal when clicking outside
    window.onclick = (e) => {
        if (e.target == modal) modal.style.display = 'none';
    }

    // Add domain handler
    addDomainBtn.addEventListener('click', async () => {
        const domain = domainInput.value.trim();
        if (!domain) return;

        try {
            addDomainBtn.disabled = true;
            addDomainBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

            const response = await fetch('/api/domains', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ domain })
            });

            const data = await response.json();

            if (response.ok) {
                // Show verification modal
                document.getElementById('verificationToken').textContent = data.instructions.txt_record;
                const stepsList = document.getElementById('verificationSteps');
                stepsList.innerHTML = data.instructions.steps.map(step => 
                    `<li>${step}</li>`
                ).join('');
                
                modal.style.display = 'block';
                domainInput.value = '';
                
                // Add domain to the list without refreshing
                const domainsList = document.querySelector('.domains-list');
                domainsList.insertAdjacentHTML('afterbegin', `
                    <div class="domain-item">
                        <div class="domain-info">
                            <span class="domain-name">${domain}</span>
                            <span class="domain-status pending">Pending Verification</span>
                        </div>
                        <button class="btn btn-verify" data-domain-id="${data.domain_id}">
                            <i class="fas fa-check"></i> Verify
                        </button>
                    </div>
                `);
            } else {
                throw new Error(data.error || 'Failed to add domain');
            }
        } catch (error) {
            alert(error.message);
        } finally {
            addDomainBtn.disabled = false;
            addDomainBtn.innerHTML = '<i class="fas fa-plus"></i> Add Domain';
        }
    });

    // Verify domain handler
    document.addEventListener('click', async (e) => {
        if (!e.target.matches('.btn-verify')) return;
        
        const button = e.target;
        const domainId = button.dataset.domainId;
        
        try {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';

            const response = await fetch(`/api/domains/${domainId}/verify`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                const domainItem = button.closest('.domain-item');
                domainItem.querySelector('.domain-status')
                    .className = 'domain-status verified';
                domainItem.querySelector('.domain-status')
                    .textContent = 'Verified';
                button.remove();
                
                // Add domain to the domain select dropdown
                const domainSelect = document.getElementById('domainSelect');
                const option = document.createElement('option');
                option.value = domainId;
                option.textContent = domainItem.querySelector('.domain-name').textContent;
                domainSelect.appendChild(option);
            } else {
                throw new Error(data.error || 'Verification failed');
            }
        } catch (error) {
            alert(error.message);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-check"></i> Verify';
        }
    });

    // Copy verification token
    document.querySelectorAll('.btn-copy').forEach(button => {
        button.addEventListener('click', async () => {
            const targetId = button.dataset.clipboardTarget;
            const text = document.querySelector(targetId).textContent;
            
            try {
                await navigator.clipboard.writeText(text);
                const icon = button.querySelector('i');
                icon.className = 'fas fa-check';
                setTimeout(() => {
                    icon.className = 'fas fa-copy';
                }, 2000);
            } catch (err) {
                alert('Failed to copy to clipboard');
            }
        });
    });
}); 