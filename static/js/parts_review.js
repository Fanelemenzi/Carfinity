// Parts Review Interface JavaScript
// Handles AJAX interactions for parts management and quote requests

class PartsReviewManager {
    constructor(assessmentId, csrfToken) {
        this.assessmentId = assessmentId;
        this.csrfToken = csrfToken;
        this.selectedParts = new Set();
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateSelectionCount();
    }
    
    bindEvents() {
        // Part selection checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('part-checkbox')) {
                this.handlePartSelection(e.target);
            }
        });
        
        // Part field updates
        document.addEventListener('change', (e) => {
            if (e.target.hasAttribute('data-part-id')) {
                this.handlePartFieldUpdate(e.target);
            }
        });
        
        // Provider selection
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('provider-checkbox')) {
                this.updateProviderSelection();
            }
        });
    }
    
    handlePartSelection(checkbox) {
        const partId = checkbox.getAttribute('data-part-id');
        
        if (checkbox.checked) {
            this.selectedParts.add(partId);
        } else {
            this.selectedParts.delete(partId);
        }
        
        this.updateSelectionCount();
        this.updateSelectedPartsSummary();
    }
    
    handlePartFieldUpdate(field) {
        const partId = field.getAttribute('data-part-id');
        const fieldName = field.getAttribute('onchange').match(/updatePartField\(this, '(.+)'\)/)[1];
        const value = field.value;
        
        this.updatePartField(partId, fieldName, value);
    }
    
    updatePartField(partId, fieldName, value) {
        const formData = new FormData();
        formData.append('action', 'update_part');
        formData.append('part_id', partId);
        formData.append('field', fieldName);
        formData.append('value', value);
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        
        fetch(`/assessments/${this.assessmentId}/parts-review/api/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showMessage(data.message, 'success');
            } else {
                this.showMessage(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error updating part:', error);
            this.showMessage('Error updating part', 'error');
        });
    }
    
    updateSelectionCount() {
        const countElement = document.getElementById('selection-count');
        if (countElement) {
            countElement.textContent = this.selectedParts.size;
        }
    }
    
    updateSelectedPartsSummary() {
        const summaryElement = document.getElementById('selected-parts-summary');
        if (!summaryElement) return;
        
        if (this.selectedParts.size === 0) {
            summaryElement.innerHTML = '<p class="text-sm text-gray-500 text-center">No parts selected</p>';
            return;
        }
        
        let summaryHtml = '<div class="space-y-2">';
        this.selectedParts.forEach(partId => {
            const partElement = document.querySelector(`[data-part-id="${partId}"]`).closest('.part-item');
            const partName = partElement.querySelector('.part-name').value;
            const partCategory = partElement.querySelector('.part-category').value;
            const damageSeverity = partElement.querySelector('.damage-severity').value;
            
            summaryHtml += `
                <div class="flex items-center justify-between text-sm">
                    <span class="font-medium">${partName}</span>
                    <span class="text-gray-500">${partCategory} - ${damageSeverity}</span>
                </div>
            `;
        });
        summaryHtml += '</div>';
        
        summaryElement.innerHTML = summaryHtml;
    }
    
    updateProviderSelection() {
        const checkboxes = document.querySelectorAll('.provider-checkbox:checked');
        const selectedProviders = Array.from(checkboxes).map(cb => cb.value);
        
        // Update UI to show selected providers
        console.log('Selected providers:', selectedProviders);
    }
    
    showMessage(message, type) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Global functions called from HTML
let partsManager;

function initPartsReview(assessmentId, csrfToken) {
    partsManager = new PartsReviewManager(assessmentId, csrfToken);
}

function identifyParts() {
    if (!partsManager) return;
    
    const formData = new FormData();
    formData.append('action', 'identify_parts');
    formData.append('csrfmiddlewaretoken', partsManager.csrfToken);
    
    fetch(`/assessments/${partsManager.assessmentId}/parts-review/api/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            partsManager.showMessage(data.message, 'success');
            // Reload page to show new parts
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            partsManager.showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error identifying parts:', error);
        partsManager.showMessage('Error identifying parts', 'error');
    });
}

function addNewPart() {
    const modal = document.getElementById('addPartModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeAddPartModal() {
    const modal = document.getElementById('addPartModal');
    if (modal) {
        modal.classList.add('hidden');
        // Reset form
        document.getElementById('addPartForm').reset();
    }
}

function saveNewPart() {
    if (!partsManager) return;
    
    const form = document.getElementById('addPartForm');
    const formData = new FormData(form);
    formData.append('action', 'add_part');
    formData.append('csrfmiddlewaretoken', partsManager.csrfToken);
    
    fetch(`/assessments/${partsManager.assessmentId}/parts-review/api/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            partsManager.showMessage(data.message, 'success');
            closeAddPartModal();
            // Reload page to show new part
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            partsManager.showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error adding part:', error);
        partsManager.showMessage('Error adding part', 'error');
    });
}

function selectAllParts() {
    const checkboxes = document.querySelectorAll('.part-checkbox');
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = !allSelected;
        if (partsManager) {
            partsManager.handlePartSelection(checkbox);
        }
    });
}

function updatePartField(element, fieldName) {
    // This function is called from HTML onchange events
    // The actual update is handled by the event listener in bindEvents
}

function updateSelectionCount() {
    if (partsManager) {
        partsManager.updateSelectionCount();
    }
}

function editPartDetails(partId) {
    // Focus on the part name field for editing
    const partElement = document.querySelector(`[data-part-id="${partId}"]`).closest('.part-item');
    const nameField = partElement.querySelector('.part-name');
    if (nameField) {
        nameField.focus();
        nameField.select();
    }
}

function removePart(partId) {
    if (!partsManager) return;
    
    if (!confirm('Are you sure you want to remove this part?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'remove_part');
    formData.append('part_id', partId);
    formData.append('csrfmiddlewaretoken', partsManager.csrfToken);
    
    fetch(`/assessments/${partsManager.assessmentId}/parts-review/api/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            partsManager.showMessage(data.message, 'success');
            // Remove the part element from DOM
            const partElement = document.querySelector(`[data-part-id="${partId}"]`).closest('.part-item');
            if (partElement) {
                partElement.remove();
            }
            partsManager.selectedParts.delete(partId);
            partsManager.updateSelectionCount();
            partsManager.updateSelectedPartsSummary();
        } else {
            partsManager.showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error removing part:', error);
        partsManager.showMessage('Error removing part', 'error');
    });
}

function previewQuoteRequest() {
    if (!partsManager || partsManager.selectedParts.size === 0) {
        partsManager.showMessage('Please select at least one part', 'error');
        return;
    }
    
    const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
    if (selectedProviders.length === 0) {
        partsManager.showMessage('Please select at least one provider', 'error');
        return;
    }
    
    // Show preview modal or summary
    alert(`Preview: ${partsManager.selectedParts.size} parts selected for ${selectedProviders.length} providers`);
}

function sendQuoteRequests() {
    if (!partsManager || partsManager.selectedParts.size === 0) {
        partsManager.showMessage('Please select at least one part', 'error');
        return;
    }
    
    const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked')).map(cb => cb.value);
    if (selectedProviders.length === 0) {
        partsManager.showMessage('Please select at least one provider', 'error');
        return;
    }
    
    if (!confirm(`Send quote requests for ${partsManager.selectedParts.size} parts to ${selectedProviders.length} providers?`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('action', 'create_quote_requests');
    formData.append('csrfmiddlewaretoken', partsManager.csrfToken);
    
    // Add selected parts
    partsManager.selectedParts.forEach(partId => {
        formData.append('selected_parts[]', partId);
    });
    
    // Add selected providers
    selectedProviders.forEach(provider => {
        formData.append('providers[]', provider);
    });
    
    fetch(`/assessments/${partsManager.assessmentId}/parts-review/api/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            partsManager.showMessage(data.message, 'success');
            // Clear selections
            partsManager.selectedParts.clear();
            document.querySelectorAll('.part-checkbox').forEach(cb => cb.checked = false);
            document.querySelectorAll('.provider-checkbox').forEach(cb => cb.checked = false);
            partsManager.updateSelectionCount();
            partsManager.updateSelectedPartsSummary();
        } else {
            partsManager.showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error sending quote requests:', error);
        partsManager.showMessage('Error sending quote requests', 'error');
    });
}