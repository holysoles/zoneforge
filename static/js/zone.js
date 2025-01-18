// Button display helper
function setButtonsDisplay(row, isEditing) {
    row.querySelector('.edit').style.display = isEditing ? 'none' : 'block';
    row.querySelector('.delete').style.display = isEditing ? 'none' : 'block';
    row.querySelector('.save').style.display = isEditing ? 'block' : 'none';
    row.querySelector('.cancel').style.display = isEditing ? 'block' : 'none';
}

// Data extraction helper
function getRecordDataFromCell(dataCell) {
    const input = dataCell.querySelector('input');
    if (input) {
        return input.value.split(':')[1]?.trim() || input.value.trim();
    }
    const text = dataCell.textContent.trim();
    return text.includes(':') ? text.split(':')[1].trim() : text;
}

// Event handlers
document.querySelectorAll('.actions button').forEach(button => {
    button.addEventListener('click', async (e) => {
        e.preventDefault();
        const row = button.closest('tr');
        
        if (button.classList.contains('edit')) {
            startEditing(row);
        } else if (button.classList.contains('save')) {
            await saveChanges(row);
        } else if (button.classList.contains('cancel')) {
            cancelEditing(row);
        } else if (button.classList.contains('delete')) {
            await deleteRecord(row);
        }
    });
});

function startEditing(row) {
    row.querySelectorAll('.editable').forEach(cell => {
        const originalText = cell.textContent.trim();
        cell.setAttribute('data-original', originalText);
        
        const input = document.createElement('input');
        input.type = 'text';
        input.value = cell.getAttribute('data-field') === 'data' 
            ? originalText.split(':')[1]?.trim() || originalText
            : originalText;
        
        // Add keypress handler for Enter key
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                await saveChanges(row);
            }
        });
        
        cell.textContent = '';
        cell.appendChild(input);
    });
    setButtonsDisplay(row, true);
}

function cancelEditing(row) {
    row.querySelectorAll('.editable').forEach(cell => {
        cell.textContent = cell.getAttribute('data-original');
    });
    setButtonsDisplay(row, false);
}

async function deleteRecord(row) {
    if (!confirm('Are you sure you want to delete this record?')) {
        return;
    }

    try {
        const response = await fetch(row.getAttribute('data-url'), {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_type: row.querySelector('[data-field="type"]').textContent.trim(),
                record_data: getRecordDataFromCell(row.querySelector('[data-field="data"]'))
            })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        row.remove();
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to delete record. Please try again.');
    }
}

async function saveChanges(row) {
    try {
        const response = await fetch(row.getAttribute('data-url'), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_type: row.querySelector('[data-field="type"] input').value,
                record_data: getRecordDataFromCell(row.querySelector('[data-field="data"]')),
                record_comment: row.querySelector('[data-field="comment"] input')?.value || ''
            })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        row.querySelectorAll('.editable').forEach(cell => {
            cell.textContent = cell.querySelector('input').value;
        });
        setButtonsDisplay(row, false);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to save changes. Please try again.');
        cancelEditing(row);
    }
}