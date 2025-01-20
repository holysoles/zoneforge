document.addEventListener('DOMContentLoaded', () => {
    // Handle modal background clicks
    document.querySelectorAll('.modal').forEach(modal => 
        modal.addEventListener('click', e => {
            if (e.target === modal) {
                modal.querySelector('form')?.reset();
                modal.classList.remove('modal-active');
            }
        })
    );

    // Handle form submissions
    document.querySelectorAll('.modal form').forEach(form => 
        form.addEventListener('submit', async e => {
            e.preventDefault();
            
            try {
                const response = await fetch(
                    form.getAttribute('data-api-endpoint'),
                    {
                        method: form.getAttribute('data-api-method') || 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(Object.fromEntries(new FormData(form)))
                    }
                );
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || `HTTP error! status: ${response.status}`);
                }
                
                window.location.reload();
            } catch (error) {
                console.error('Error:', error);
                alert(`Failed to submit form: ${error.message}`);
            }
        })
    );

    // Handle delete button clicks
    document.querySelectorAll('input[type="delete"]').forEach(deleteButton => 
        deleteButton.addEventListener('click', async e => {
            e.preventDefault();

            const form = deleteButton.closest('form');
            const apiEndpoint = deleteButton.getAttribute('data-api-endpoint');
            const apiId = deleteButton.getAttribute('data-api-id');
            const redirectUrl = deleteButton.getAttribute('data-delete-redirect');
            const idValue = form.querySelector(`#${apiId}`)?.value;

            if (!confirm(`Are you sure you want to delete '${idValue}'?`)) {
                return;
            }

            try {
                const response = await fetch(
                    `${apiEndpoint}${idValue ? '/' + idValue : ''}`,
                    {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' }
                    }
                );
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || `HTTP error! status: ${response.status}`);
                }
                
                window.location.href = redirectUrl;
            } catch (error) {
                console.error('Error:', error);
                alert(`Failed to delete: ${error.message}`);
            }
        })
    );
}); 