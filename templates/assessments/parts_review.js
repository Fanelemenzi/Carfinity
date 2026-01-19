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
                this.updateSelectionCount();
            }
        });

        // Provider selection checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('provider-checkbox')) {
                this.updateProviderSelection();
            }
        });

        // Form submissions
        const addPartForm = document.getElementById('addPartForm');
        if (addPartForm) {
            addPartForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleAddPart();
            });
        }

        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.id === 'addPartModal') {
                this.closeAddPartModal();
            }
        });

        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAddPartModal();
            }
        });
    }

    // Parts identification
    async identifyParts() {
        this.showLoading();

        try {
            const response = await fetch(`/insurance/api/assessments/${this.assessmentId}/identify-parts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                }
            });

            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.showSuccessMessage(`Successfully identified ${data.parts_count} damaged parts`);
                setTimeout(() => location.reload(), 1500);
            } else {
                this.showErrorMessage('Error identifying parts: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error:', error);
            this.showErrorMessage('Error identifying parts. Please try again.');
        }
    }

    // Update part field
    async updatePartField(element, fieldName) {
        const partId = element.dataset.partId;
        const value = element.value;
        const originalValue = element.defaultValue;

        try {
            const response = await fetch(`/insurance/api/damaged-parts/${partId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    [fieldName]: value
                })
            });

            const data = await response.json();

            if (!data.success) {
                this.showErrorMessage('Error updating part: ' + (data.message || 'Unknown error'));
                element.value = originalValue; // Revert the change
            } else {
                // Visual feedback for successful update
                element.classList.add('border-green-300');
                setTimeout(() => {
                    element.classList.remove('border-green-300');
                }, 1000);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showErrorMessage('Error updating part. Please try again.');
            element.value = originalValue;
        }
    }

    // Selection management
    updateSelectionCount() {
        const checkboxes = document.querySelectorAll('.part-checkbox:checked');
        const count = checkboxes.length;

        const countElement = document.getElementById('selection-count');
        if (countElement) {
            countElement.textContent = count;
        }

        // Update selected parts summary
        this.updateSelectedPartsSummary(checkboxes);
    }

    updateSelectedPartsSummary(checkboxes) {
        const summaryDiv = document.getElementById('selected-parts-summary');
        if (!summaryDiv) return;

        if (checkboxes.length === 0) {
            summaryDiv.innerHTML = '<p class="text-sm text-gray-500 text-center">No parts selected</p>';
        } else {
            let summaryHtml = '<div class="space-y-2">';
            checkboxes.forEach(checkbox => {
                const partItem = checkbox.closest('.part-item');
                const partName = partItem.querySelector('.part-name').value;
                const partCategory = partItem.querySelector('.part-category').value;
                const severity = partItem.querySelector('.damage-severity').value;

                summaryHtml += `
                    <div class="flex items-center justify-between text-sm">
                        <span class="font-medium">${partName}</span>
                        <div class="flex items-center space-x-2">
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">${this.formatCategory(partCategory)}</span>
                            <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">${this.formatSeverity(severity)}</span>
                        </div>
                    </div>
                `;
            });
            summaryHtml += '</div>';
            summaryDiv.innerHTML = summaryHtml;
        }
    }

    selectAllParts() {
        const checkboxes = document.querySelectorAll('.part-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
        });

        this.updateSelectionCount();
    }

    // Add new part
    showAddPartModal() {
        const modal = document.getElementById('addPartModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeAddPartModal() {
        const modal = document.getElementById('addPartModal');
        if (modal) {
            modal.classList.add('hidden');
        }

        const form = document.getElementById('addPartForm');
        if (form) {
            form.reset();
        }
    }

    async handleAddPart() {
        const formData = {
            part_name: document.getElementById('new-part-name').value,
            part_category: document.getElementById('new-part-category').value,
            damage_severity: document.getElementById('new-damage-severity').value,
            estimated_labor_hours: document.getElementById('new-labor-hours').value || 0,
            section_type: document.getElementById('new-section-type').value,
            part_number: document.getElementById('new-part-number').value,
            damage_description: document.getElementById('new-damage-description').value
        };

        // Validate required fields
        const requiredFields = ['part_name', 'part_category', 'damage_severity', 'damage_description'];
        for (const field of requiredFields) {
            if (!formData[field]) {
                this.showErrorMessage(`Please fill in the ${field.replace('_', ' ')}`);
                return;
            }
        }

        this.showLoading();

        try {
            const response = await fetch(`/insurance/api/assessments/${this.assessmentId}/damaged-parts/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.closeAddPartModal();
                this.showSuccessMessage('Part added successfully');
                setTimeout(() => location.reload(), 1500);
            } else {
                this.showErrorMessage('Error adding part: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error:', error);
            this.showErrorMessage('Error adding part. Please try again.');
        }
    }

    // Remove part
    async removePart(partId) {
        if (!confirm('Are you sure you want to remove this part?')) {
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/insurance/api/damaged-parts/${partId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                const partElement = document.querySelector(`[data-part-id="${partId}"]`);
                if (partElement) {
                    partElement.remove();
                }
                this.updateSelectionCount();
                this.showSuccessMessage('Part removed successfully');
            } else {
                this.showErrorMessage('Error removing part: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error:', error);
            this.showErrorMessage('Error removing part. Please try again.');
        }
    }

    // Quote request functions
    previewQuoteRequest() {
        const selectedPartIds = this.getSelectedPartIds();
        const selectedProviders = this.getSelectedProviders();

        if (selectedPartIds.length === 0) {
            this.showErrorMessage('Please select at least one part for the quote request.');
            return;
        }

        if (selectedProviders.length === 0) {
            this.showErrorMessage('Please select at least one provider for the quote request.');
            return;
        }

        // Show preview information
        const message = `Preview: ${selectedPartIds.length} parts selected for ${selectedProviders.length} providers\n\nParts: ${selectedPartIds.length}\nProviders: ${selectedProviders.join(', ')}`;
        alert(message);
    }

    async sendQuoteRequests() {
        const selectedPartIds = this.getSelectedPartIds();
        const selectedProviders = this.getSelectedProviders();

        if (selectedPartIds.length === 0) {
            this.showErrorMessage('Please select at least one part for the quote request.');
            return;
        }

        if (selectedProviders.length === 0) {
            this.showErrorMessage('Please select at least one provider for the quote request.');
            return;
        }

        if (!confirm(`Send quote requests for ${selectedPartIds.length} parts to ${selectedProviders.length} providers?`)) {
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/insurance/api/assessments/${this.assessmentId}/quote-requests/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    part_ids: selectedPartIds,
                    providers: selectedProviders
                })
            });

            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.showSuccessMessage(`Quote requests sent successfully! ${data.requests_created} requests created.`);
                // Navigate to quote tracking page after delay
                setTimeout(() => {
                    window.location.href = `/assessments/${this.assessmentId}/quote-requests/`;
                }, 2000);
            } else {
                this.showErrorMessage('Error sending quote requests: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            this.hideLoading();
            console.error('Error:', error);
            this.showErrorMessage('Error sending quote requests. Please try again.');
        }
    }

    // Helper methods
    getSelectedPartIds() {
        return Array.from(document.querySelectorAll('.part-checkbox:checked'))
            .map(cb => cb.dataset.partId);
    }

    getSelectedProviders() {
        return Array.from(document.querySelectorAll('.provider-checkbox:checked'))
            .map(cb => cb.value);
    }

    formatCategory(category) {
        const categoryMap = {
            'body': 'Body Panel',
            'mechanical': 'Mechanical',
            'electrical': 'Electrical',
            'glass': 'Glass',
            'interior': 'Interior',
            'trim': 'Trim',
            'wheels': 'Wheels',
            'safety': 'Safety',
            'structural': 'Structural',
            'fluid': 'Fluid'
        };
        return categoryMap[category] || category;
    }

    formatSeverity(severity) {
        const severityMap = {
            'minor': 'Minor',
            'moderate': 'Moderate',
            'severe': 'Severe',
            'replace': 'Replace'
        };
        return severityMap[severity] || severity;
    }

    // UI utility methods
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type = 'info') {
        // Create a temporary message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
                'bg-blue-100 text-blue-800 border border-blue-200'
            }`;

        messageDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-exclamation-circle' :
                    'fa-info-circle'
            } mr-2"></i>
                <span class="text-sm font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(messageDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// Global functions for template compatibility
let partsManager;

function identifyParts() {
    if (partsManager) {
        partsManager.identifyParts();
    }
}

function updatePartField(element, fieldName) {
    if (partsManager) {
        partsManager.updatePartField(element, fieldName);
    }
}

function selectAllParts() {
    if (partsManager) {
        partsManager.selectAllParts();
    }
}

function addNewPart() {
    if (partsManager) {
        partsManager.showAddPartModal();
    }
}

function closeAddPartModal() {
    if (partsManager) {
        partsManager.closeAddPartModal();
    }
}

function removePart(partId) {
    if (partsManager) {
        partsManager.removePart(partId);
    }
}

function previewQuoteRequest() {
    if (partsManager) {
        partsManager.previewQuoteRequest();
    }
}

function sendQuoteRequests() {
    if (partsManager) {
        partsManager.sendQuoteRequests();
    }
}

function editPartDetails(partId) {
    // Navigate to detailed part editing page or show modal
    alert(`Edit part details for part ID: ${partId}`);
}

function updateSelectionCount() {
    if (partsManager) {
        partsManager.updateSelectionCount();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Get assessment ID and CSRF token from template
    const assessmentId = window.assessmentId;
    const csrfToken = window.csrfToken;

    if (assessmentId && csrfToken) {
        partsManager = new PartsReviewManager(assessmentId, csrfToken);
    }
});