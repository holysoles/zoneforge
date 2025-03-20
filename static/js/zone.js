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
    let returnDict = {};
    dataCellList.forEach(dataCell => {
        let data = '';
        const input = dataCell.querySelector('input');
        if (input) {
            data = input.value.trim();
        } else {
            data = dataCell.textContent.trim();
        }

        let label = dataCell.previousSibling.textContent.trim();
        // remove the colon, downcase everything
        label = label.replace(':', '').toLowerCase();

        returnDict[label] = data;
    });
    return returnDict;
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
        
        if (cell.getAttribute('data-field') === 'type') {
            // Create select dropdown for record type
            const select = document.createElement('select');
            // Clone the options from the new record row's select
            const templateSelect = document.querySelector('.new-record [data-field="type"] select');
            templateSelect.querySelectorAll('option').forEach(option => {
                const newOption = option.cloneNode(true);
                select.appendChild(newOption);
            });
            // Set the current value
            select.value = originalText;
            cell.textContent = '';
            cell.appendChild(select);
        } else if (cell.getAttribute('data-field') === 'data') {
            // For data cells, create a new input in the existing structure
            const input = document.createElement('input');
            input.type = 'text';
            input.value = originalText;
            cell.textContent = '';
            cell.appendChild(input);
            
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
    // Restore original text content for non-data fields
    row.querySelectorAll('.editable:not([data-field="data"])').forEach(cell => {
        cell.textContent = cell.getAttribute('data-original');
    });
    
    // Restore original data entries
    row.querySelectorAll('.editable[data-field="data"]').forEach(cell => {
        const originalText = cell.getAttribute('data-original');
        if (originalText) {
            cell.textContent = originalText;
        }
    });
    
    // Remove any additional data entries that were added during editing
    const dataRows = row.querySelector('.data-rows');
    if (dataRows) {
        dataRows.querySelectorAll('.data-entry').forEach(entry => {
            if (!entry.querySelector('[data-original]')) {
                entry.remove();
            }
        });
    }
    
    setButtonsDisplay(row, false);
}

async function deleteRecord(row) {
    if (!confirm('Are you sure you want to delete this record?')) {
        return;
    }

    try {
        const requestBody = Object.fromEntries([
            ['type', row.querySelector('[data-field="type"]').textContent.trim()],
            ['ttl', row.querySelector('[data-field="ttl"]')?.textContent.trim()],
            ['data', getRecordDataFromCell(row.querySelectorAll('[data-field="data"]'))],
            ['comment', row.querySelector('[data-field="comment"]')?.textContent.trim()],
            ['index', row.getAttribute('data-record-index')]
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
            ['type', row.querySelector('[data-field="type"] select')?.value.trim()],
            ['ttl', row.querySelector('[data-field="ttl"] input')?.value.trim()],
            ['data', getRecordDataFromCell(row.querySelectorAll('[data-field="data"]'))],
            ['comment', row.querySelector('[data-field="comment"] input')?.value.trim()],
            ['index', row.getAttribute('data-record-index')]
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

        // Update the row with the new values
        row.querySelectorAll('.editable').forEach(cell => {
            cell.textContent = cell.querySelector('input,select').value;
        });
        setButtonsDisplay(row, false);
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to save changes: ${error.message}`);
        cancelEditing(row);
    }
}

// helper function to add an enter key handler to a row
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

// Allow Submitting a new record on Enter key press
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
                ['type', row.querySelector('[data-field="type"] select')?.value.trim()],
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

// helper function to create a new row element for record data fields (e.g. Address, Target, etc)
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
    
    div.appendChild(pLabel);
    div.appendChild(pData);
    return div;
}

// helper function to format a labels generically (e.g. address_name -> Address Name)
function formatLabel(label) {
    return label
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
}

async function updateDataFieldsForType(typeSelect) {
    const selectedType = typeSelect.value;
    const row = typeSelect.closest('tr');
    const dataRows = row.querySelector('.data-rows');
    const existingEntries = dataRows.querySelectorAll('.data-entry');

    try {
        const response = await fetch(`/api/types/recordtype/${selectedType}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const recordTypeData = await response.json();
        const fieldLabels = recordTypeData.fields || [];
        
        // Remove any non-primary empty rows
        existingEntries.forEach((entry, index) => {
            if (index > 0) { // Skip the first/primary row
                const input = entry.querySelector('input');
                if (input && !input.value.trim()) {
                    entry.remove();
                }
            }
        });

        // Get fresh list of entries after removal
        const remainingEntries = dataRows.querySelectorAll('.data-entry');
        
        // Update labels for remaining entries
        remainingEntries.forEach((entry, index) => {
            const label = entry.querySelector('.data-row-label');
            const fieldLabel = fieldLabels[index] || '';
            if (fieldLabel) {
                const formattedLabel = formatLabel(fieldLabel);
                label.textContent = formattedLabel + ':';
            } else {
                label.textContent = '';
            }
        });

        // Add new rows if we need more
        for (let i = remainingEntries.length; i < fieldLabels.length; i++) {
            const newRow = createDataRowInput();
            const label = newRow.querySelector('.data-row-label');
            const fieldLabel = fieldLabels[i];
            const formattedLabel = formatLabel(fieldLabel);
            label.textContent = formattedLabel + ':';
            dataRows.appendChild(newRow);
        }

    } catch (error) {
        console.error('Error fetching record type data:', error);
    }
}

// Add event listeners for record type selectors
document.querySelectorAll('[data-field="type"] select').forEach(select => {
    select.addEventListener('change', () => updateDataFieldsForType(select));
});
// run once on page load for the new record row
document.querySelectorAll('.new-record select').forEach(select => {
    updateDataFieldsForType(select);
});
