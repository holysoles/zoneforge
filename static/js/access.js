
// Event handlers
document.querySelectorAll('.actions button').forEach(button => {
    button.addEventListener('click', async (e) => {
        e.preventDefault();
        const row = button.closest('tr, form');
        
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
        let originalText = undefined
        if (cell.childElementCount) {
            originalText = Array.from(cell.querySelectorAll("span")).map(role => role.textContent).join();
        } else {
            originalText = cell.textContent.trim();
        }
        
        cell.setAttribute('data-original', originalText);
        
        if (cell.getAttribute('data-field') === 'group') {
            // Copy select dropdown for groups (user tab)
            const select = document.querySelector(".select-content select")
            const newSelect = select.cloneNode(true);
            const selectedIndex = Array.from(newSelect.options).findIndex(selected => selected.textContent === originalText)
            selectedIndex > 0 && (newSelect.selectedIndex = selectedIndex)

            newSelect.style.position = "relative"
            newSelect.style.width = 0
            newSelect.style.cursor = "pointer"

            cell.textContent = '';
            cell.appendChild(newSelect);

        } else if (cell.getAttribute('data-field') === 'role') {
            // Copy select dropdown for roles (group tab)
            const selectContent = document.querySelector(".select-content")
            const newSelect = selectContent.cloneNode(true)
            const displaySelectedRoles = newSelect.querySelector("#display-selected-roles")

            newSelect.firstChild.remove()
            
            for (const option of newSelect.querySelectorAll("option")) {
                option.selected = originalText.split(",").includes(option.textContent)
            }

            newSelect.querySelector(".drop-select").setAttribute("onclick", "document.querySelector('tbody #access-options').classList.toggle('access-options-active')")
            
            cell.style.overflow = "visible"
            cell.textContent = '';
            
            const select = newSelect.querySelector("select")
            select && select.addEventListener("change", (event) => changeMultiSelect(event))

            cell.appendChild(newSelect);

            originalText && displayRoles(displaySelectedRoles, originalText.split(","))
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
    // Restore original text content for non-role fields
    row.querySelectorAll('.editable:not([data-field="role"])').forEach(cell => {
        cell.textContent = cell.getAttribute('data-original');
    });
    
    // Restore original role entries (group tab: list from roles)
    row.querySelectorAll('.editable[data-field="role"]').forEach(cell => {
        const originalText = cell.getAttribute('data-original');
        displayRoles(cell, originalText.split(",").filter(value => value))
        cell.style.overflow = "auto"
    });
    
    setButtonsDisplay(row, false);
}

async function deleteRecord(row) {
    if (!confirm('Are you sure you want to delete this record?')) {
        return;
    }

    try {
        const name = row.querySelector("[data-name-url]")
        const deleteRecord = {
            tag: name.textContent,
            url: name.dataset.nameUrl,
            method: "DELETE",
        }

        const response = await fetchWithBaseConfig(deleteRecord)
        handleError(response)

        alert(`${response.tag}: ${response.message}`)

        row.remove();
    } catch (error) {
        console.error('Error:', error);
        alert(`${error.tag}: ${error.message}` || `HTTP error! status: ${response.status}`);
    }
}

async function saveChanges(row) {
    try {
        const bodyNameKey = row.dataset.category == "users"? "username": "name"
        const name = row.querySelector('.editable[data-field="name"]')
        const update = [
            {
                tag: name.firstChild.value,
                url: name.dataset.nameUrl,
                method: row.dataset.category == "users"? "PATCH": "PUT",
                options: {
                    body: JSON.stringify({
                        [bodyNameKey]: row.querySelector("[data-field='name'] input").value
                    })
                }
            },
        ]
        const select = row.querySelector("[data-field='group'] select, [data-field='role'] select")
        const selectedOptions = Array.from((select && select.selectedOptions) || []).filter(option => option.value)

        const group = row.querySelector('.editable[data-field="group"]')
        if (row.dataset.category == "users" && selectedOptions.length) {
            update.push({
                tag: selectedOptions[0].textContent,
                url: group.dataset.selectUrl.replace(/0$/, selectedOptions[0].value),
                method: group.dataset.original == "None"? "POST": "PUT",
            })
        }
        
        const roles = row.querySelector('.editable[data-field="role"]')
        if (row.dataset.category == "groups") {
            for (const option of select) {
                const previousRoles = roles.dataset.original.split(",")
                const selectedText = Array.from(selectedOptions).map(option => option.textContent)

                // Validate roles to delete, create or not make any action if already exist
                if (previousRoles.includes(option.textContent) && !selectedText.includes(option.textContent)) {
                    update.push({
                        tag: option.textContent,
                        url: row.querySelector("[data-select-url]").dataset.selectUrl.replace(/0$/, option.value),
                        method: "DELETE",
                    })
                } else if (!previousRoles.includes(option.textContent) && selectedText.includes(option.textContent)) {
                    update.push({
                        tag: option.textContent,
                        url: row.querySelector("[data-select-url]").dataset.selectUrl.replace(/0$/, option.value),
                        method: "POST",
                    })
                }
            }
        }  
        
        const response = []

        for (let request of update) {
            response.push(await fetchWithBaseConfig(request))
        }

        response.forEach(res => {
            handleError(res, response)
        })

        alert(response.map(res => `${res.tag}: ${res.message}\n`).join(""))

        // Update the row with the new values
        name.textContent = name.querySelector('input').value

        group && (group.textContent = select.selectedIndex? select.selectedOptions[0].textContent: group.dataset.original)

        if(roles) {
            roles.textContent = ""
            displayRoles(roles, Array.from(selectedOptions).map(role => role.textContent))
            roles.style.overflow = "auto"
        }

        setButtonsDisplay(row, false);
    } catch (error) {
        console.error('Error:', error);
        if (error.details) {
            alert(error.details.map(res => `${res.tag}: ${res.message}\n`).join(""));
            window.location.reload();
        } else {
            alert(`${error.message}` || `HTTP error! status: ${response.status}`)
        }
    }
}

async function createRecord(row) {
    try {
        const bodyNameKey = row.dataset.category == "users"? "username": "name"
        const passwordElement = row.querySelector("[data-field='password']")
        const password = {password: (passwordElement && passwordElement.value) || "123456"}
        const name = row.querySelector("[data-field='name']").value
        const create = [
            {
                tag: name,
                url: row.dataset.url,
                method: "POST",
                options: {
                    body: JSON.stringify({
                        [bodyNameKey]: name,
                        ...(row.dataset.category == "users" && password)
                    })
                }
            }
        ]

        const response = []

        // Fetch to create resource id to assign group or role and validate creation 
        response.push(await fetchWithBaseConfig(create[0]))
        handleError(response[0], response)

        const select = row.querySelector("#access-options")
        const selectOptions = (select && select.selectedOptions) || []
        for (const option of Array.from(selectOptions).filter(option => option.value)) {
            create.push({
                tag: option.textContent,
                url: option.dataset.optionUrl.replace("0", response[0].id).replace("0", option.value),
                method: "POST",
            })
        }

        for (let request of create.filter((_, index) => index > 0 )) {
            response.push(await fetchWithBaseConfig(request))
        }

        response.forEach(res => {
            handleError(res, response)
        })

        const reload = confirm(
            response.map((res, index) => {
                if(index == 0) {
                    return`${res.tag}: ${res.message}\nPassword: ${password.password}\n`
                } else {
                    return `${res.tag}: ${res.message}\n`
                }
            }).join("") +
            "\nReload to load new record?"
        )

        reload && window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        if(error.details && error.details[0].ok) {
            alert(error.details.map(res => `${res.tag}: ${res.message}\n`).join(""));
            window.location.reload();
        } else if (error.details) {
            alert(error.details.map(res => `${res.tag}: ${res.message}\n`).join(""));
        } else {
            alert(error.message || `HTTP error! status: ${response.status}`)
        }
    }
}

// Display selected roles(groups tab)
const selectMultiOptions = document.querySelector("form .access-options-inactive")
selectMultiOptions && selectMultiOptions.addEventListener("change", (event) => changeMultiSelect(event))
function changeMultiSelect(event) {
    const displaySelectedRoles = event.target.closest(".select-content").querySelector("#display-selected-roles")
    const selectedOptions = Array.from(event.target.selectedOptions).map(role => role.textContent)

    const currentRolesAndSelected = Array.from(displaySelectedRoles.children).map(inView => inView.textContent).filter(item => selectedOptions.includes(item))

    displayRoles(displaySelectedRoles, [...selectedOptions.filter(item => !currentRolesAndSelected.includes(item)), ...currentRolesAndSelected])
}

function displayRoles(displaySelectedRoles, rolesToDisplay) {
    displaySelectedRoles.innerHTML = ""
    rolesToDisplay.forEach(newSelected => {
        displaySelectedRoles.insertAdjacentHTML("beforeend", `<span class="multi-role">${newSelected}</span>`)
    })
}

// Change between system generate/user generate password(users tab)
const allowGeneratePassword = document.querySelector("#allow-generate-password")
allowGeneratePassword && allowGeneratePassword.addEventListener("change", () => {
    const generatePassword = document.querySelector("#generate-password")

    if(allowGeneratePassword.checked) {
        generatePassword.toggleAttribute("disabled")
        generatePassword.style.cursor = "text"
    } else {
        generatePassword.toggleAttribute("disabled")
        generatePassword.style.cursor = "not-allowed"
        generatePassword.value = ""
    }
})

// Button display helper
function setButtonsDisplay(row, isEditing) {
    row.querySelector('.edit').style.display = isEditing ? 'none' : 'block';
    row.querySelector('.delete').style.display = isEditing ? 'none' : 'block';
    row.querySelector('.save').style.display = isEditing ? 'block' : 'none';
    row.querySelector('.cancel').style.display = isEditing ? 'block' : 'none';
}

// helper function to add an enter key handler to a row
function addEnterKeyHandler(row, handler) {
    row.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                await handler(row);
            }
        });
    });
}

// Allow Submitting a new record on Enter key true
document.querySelectorAll('tr.new-record').forEach(row => {
    addEnterKeyHandler(row, createRecord);
});

// Fetch helper
async function fetchWithBaseConfig({url, method, options = {}, tag}) {
    const baseConfig = {
        method,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    }

    const res = await fetch(url, baseConfig)

    return {tag, ...(await res.json()), statusCode: res.status, ok: res.ok}
}

// Error helper
function handleError(res, response) {
    if(!res.ok) {
        const error = new Error(res.message || `HTTP error! status: ${res.status}`);
        error.details = response
        throw error
    }
}
