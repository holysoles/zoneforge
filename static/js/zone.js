// Add event listener for all delete buttons
document.querySelectorAll('button.delete').forEach(button => {
    button.addEventListener('click', async function(e) {
        // Prevent default button behavior
        e.preventDefault();
        
        // Get data from button attributes
        const url = this.getAttribute('data-url');
        
        // Confirm deletion with user
        if (!confirm('Are you sure you want to delete this record?')) {
            return;
        }

        try {
            // Make DELETE request to API
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    record_type: this.getAttribute('data-record-type'),
                    record_data: this.getAttribute('data-record-data')
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // On success, remove the table row
            const row = this.closest('tr');
            row.remove();

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to delete record. Please try again.');
        }
    });
});