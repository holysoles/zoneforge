// Button display helper
function setButtonsDisplay(row, isEditing) {
    if (row.classList.contains('new-record')) {
        row.querySelector('.create').style.display = isEditing ? 'none' : 'block';
    } else {
        row.querySelector('.edit').style.display = isEditing ? 'none' : 'block';
        row.querySelector('.delete').style.display = isEditing ? 'none' : 'block';
    }
    row.querySelector('.save').style.display = isEditing ? 'block' : 'none';
    row.querySelector('.cancel').style.display = isEditing ? 'block' : 'none';
}

// Data extraction helper
function getRecordDataFromCell(dataCellList) {
    let returnText = '';
    dataCellList.forEach(dataCell => {
        const input = dataCell.querySelector('input');
        if (input) {
            returnText += input.value.trim() + " ";
        } else {
            returnText += dataCell.textContent.trim() + " ";
        }
    });
    return returnText;
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
        } else if (button.classList.contains('create')) {
            await createRecord(row);
        }
    });
});

function startEditing(row) {
    row.querySelectorAll('.editable').forEach(cell => {
        const originalText = cell.textContent.trim();
        cell.setAttribute('data-original', originalText);
        
        if (cell.getAttribute('data-field') === 'data') {
            // For data cells, create a new input in the existing structure
            const input = document.createElement('input');
            input.type = 'text';
            input.value = originalText;
            cell.textContent = '';
            cell.appendChild(input);
            
            // Add the + button if it's the last data entry
            const dataEntry = cell.closest('.data-entry');
            if (dataEntry && !dataEntry.nextElementSibling) {
                const addButton = document.createElement('button');
                addButton.type = 'button';
                addButton.className = 'add-data-row';
                addButton.textContent = '+';
                addButton.onclick = (e) => {
                    e.preventDefault();
                    const newRow = createDataRowInput();
                    dataEntry.insertAdjacentElement('afterend', newRow);
                };
                dataEntry.appendChild(addButton);
            }
        } else {
            // For non-data cells, handle as before
            const input = document.createElement('input');
            input.type = 'text';
            input.value = originalText;
            cell.textContent = '';
            cell.appendChild(input);
        }
    });
    
    addEnterKeyHandler(row, saveChanges);
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
        const requestBody = Object.fromEntries([
            ['type', row.querySelector('[data-field="type"]').textContent.trim()],
            ['data', getRecordDataFromCell(row.querySelectorAll('[data-field="data"]'))]
        ].filter(([_, value]) => value));

        const response = await fetch(row.getAttribute('data-url'), {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `HTTP error! status: ${response.status}`);
        }
        row.remove();
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to delete record: ${error.message}`);
    }
}

async function saveChanges(row) {
    try {
        const requestBody = Object.fromEntries([
            ['type', row.querySelector('[data-field="type"] input')?.value.trim()],
            ['ttl', row.querySelector('[data-field="ttl"] input')?.value.trim()],
            ['data', getRecordDataFromCell(row.querySelectorAll('[data-field="data"]'))],
            ['comment', row.querySelector('[data-field="comment"] input')?.value.trim()]
        ].filter(([_, value]) => value));

        const response = await fetch(row.getAttribute('data-url'), {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `HTTP error! status: ${response.status}`);
        }

        row.querySelectorAll('.editable').forEach(cell => {
            cell.textContent = cell.querySelector('input').value;
        });
        setButtonsDisplay(row, false);
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to save changes: ${error.message}`);
        cancelEditing(row);
    }
}

// Add this new function to handle input keypress events
function addEnterKeyHandler(row, handler) {
    row.querySelectorAll('input').forEach(input => {
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                await handler(row);
            }
        });
    });
}

// Add enter key handlers to new record rows
document.querySelectorAll('tr.new-record').forEach(row => {
    addEnterKeyHandler(row, createRecord);
});

async function createRecord(row) {
    try {
        const nameInput = row.querySelector('[data-field="name"] input');
        const recordName = nameInput.value.trim();
        
        if (!recordName) {
            alert('Record name is required');
            return;
        }

        const url = row.getAttribute('data-url').replace('_new', recordName);
        
        const requestBody = Object.fromEntries(
            [
                ['type', row.querySelector('[data-field="type"] input')?.value.trim()],
                ['ttl', row.querySelector('[data-field="ttl"] input')?.value.trim()],
                ['data', getRecordDataFromCell(row.querySelectorAll('[data-field="data"]'))],
                ['comment', row.querySelector('[data-field="comment"] input')?.value.trim()]
            ].filter(([_, value]) => value)
        );
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `HTTP error! status: ${response.status}`);
        }
        
        row.querySelectorAll('input').forEach(input => input.value = '');
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to create record: ${error.message}`);
    }
}

// Add this new function to create a data row input
function createDataRowInput() {
    const div = document.createElement('div');
    div.className = 'data-entry';
    
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'data';

    // Create p element for the data-field label
    const pLabel = document.createElement('p');
    pLabel.className = 'data-row-label';
    pLabel.textContent = '';
    
    // Create p element with data-field attribute
    const pData = document.createElement('p');
    pData.className = 'data-row editable';
    pData.setAttribute('data-field', 'data');
    pData.appendChild(input);
    
    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-data-row';
    removeButton.textContent = '−';
    removeButton.onclick = (e) => {
        e.preventDefault();
        div.remove();
    };
    
    div.appendChild(pLabel);
    div.appendChild(pData);
    div.appendChild(removeButton);
    return div;
}

// Add click handler for add-data-row buttons
document.querySelectorAll('.add-data-row').forEach(button => {
    button.addEventListener('click', (e) => {
        e.preventDefault();
        const currentDataEntry = button.parentElement;
        const newRow = createDataRowInput();
        currentDataEntry.insertAdjacentElement('afterend', newRow);
    });
});