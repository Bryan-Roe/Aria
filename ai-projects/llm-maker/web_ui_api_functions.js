// Replace the mock functions in web_ui.html with these real API functions

// API Base URL
const API_BASE = '';  // Empty for same-origin requests

async function createTool() {
    const name = document.getElementById('toolName').value.trim();
    const description = document.getElementById('toolDescription').value.trim();
    const parameters = getParameters();
    const returnType = document.getElementById('returnType').value.trim() || 'Any';

    if (!name || !description) {
        showStatus('createStatus', 'Please fill in all required fields', 'error');
        return;
    }

    // Show loading
    document.getElementById('createBtn').disabled = true;
    document.getElementById('createBtnText').style.display = 'none';
    document.getElementById('createLoading').style.display = 'inline-block';

    try {
        const response = await fetch(`${API_BASE}/api/tools`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name,
                description,
                parameters,
                return_type: returnType
            })
        });

        const result = await response.json();

        if (result.success) {
            showStatus('createStatus', `Tool "${name}" created successfully!`, 'success');
            document.getElementById('createToolForm').reset();
            // Reset parameters to single row
            document.getElementById('parametersContainer').innerHTML = `
                <div class="param-row">
                    <input type="text" placeholder="Parameter name" class="param-name">
                    <input type="text" placeholder="Type (e.g., int, str)" class="param-type">
                    <button type="button" class="btn-icon" onclick="removeParam(this)">✕</button>
                </div>
            `;
            loadTools();
        } else {
            showStatus('createStatus', `Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus('createStatus', `Error: ${error.message}`, 'error');
    } finally {
        // Hide loading
        document.getElementById('createBtn').disabled = false;
        document.getElementById('createBtnText').style.display = 'inline';
        document.getElementById('createLoading').style.display = 'none';
    }
}

async function loadTools() {
    try {
        const response = await fetch(`${API_BASE}/api/tools`);
        const data = await response.json();

        tools = data.tools || [];
        updateStats(data.stats);
        renderTools();
    } catch (error) {
        console.error('Error loading tools:', error);
        showStatus('createStatus', 'Error loading tools. Is the server running?', 'error');
    }
}

async function executeTool(toolId, params) {
    try {
        const response = await fetch(`${API_BASE}/api/tools/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tool_id: toolId,
                arguments: params
            })
        });

        return await response.json();
    } catch (error) {
        return { success: false, error: error.message };
    }
}

async function deleteTool(toolId) {
    try {
        const response = await fetch(`${API_BASE}/api/tools/${toolId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            loadTools();
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error deleting tool:', error);
        return false;
    }
}
