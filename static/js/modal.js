document.addEventListener('DOMContentLoaded', () => {
    // Find all modal forms and attach submit handlers
    document.querySelectorAll('.modal form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const modalId = form.closest('.modal').id;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            try {
                const apiEndpoint = form.getAttribute('data-api-endpoint');

                const method = form.getAttribute('data-api-method') || 'POST';
                
                const response = await fetch(apiEndpoint, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.message || `HTTP error! status: ${response.status}`);
                }
                
                window.location.reload();
      
            } catch (error) {
                console.error('Error:', error);
                alert(`Failed to submit form: ${error.message}`);
            }
        });
    });
}); 