/**
 * Quote Request Dispatch Interface JavaScript
 * Handles provider selection, part selection, batch operations, and real-time updates
 */

class QuoteRequestManager {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    init() {
        this.form = document.getElementById('quote-request-form');
        this.providerCheckboxes = document.querySelectorAll('.provider-checkbox');
        this.partCheckboxes = document.querySelectorAll('.part-checkbox');
        this.dispatchBtn = document.getElementById('dispatch-btn');
        this.selectedCountSpan = document.getElementById('selected-count');
        this.providerCountSpan = document.getElementById('provider-count');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.confirmationModal = document.getElementById('confirmation-modal');
        
        // Auto-refresh interval (30 seconds)
        this.refreshInterval = 30000;
        this.refreshTimer = null;
    }

    setupEventListeners() {
        // Provider selection
        this.providerCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handleProviderSelection(e));
        });

        // Part selection
        this.partCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.handlePartSelection(e));
        });

        // Bulk selection buttons
        const selectAllBtn = document.getElementById('select-all-parts');
        const clearAllBtn = document.getElementById('clear-all-parts');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllParts());
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => this.clearAllParts());
        }

        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Confirmation modal
        this.setupConfirmationModal();

        // Cancel request buttons
        this.setupCancelRequestButtons();
    }

    handleProviderSelection(event) {
        const checkbox = event.target;
        const card = checkbox.closest('.provider-card');
        
        if (checkbox.checked) {
            card.classList.add('selected');
            this.animateSelection(card);
        } else {
            card.classList.remove('selected');
        }
        
        this.updateCounts();
        this.updateProviderRecommendations();
    }

    handlePartSelection(event) {
        const checkbox = event.target;
        const card = checkbox.closest('.part-card');
        
        if (checkbox.checked) {
            card.classList.add('selected');
            this.animateSelection(card);
        } else {
            card.classList.remove('selected');
        }
        
        this.updateCounts();
    }

    animateSelection(element) {
        element.style.transform = 'scale(1.02)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 150);
    }

    selectAllParts() {
        this.partCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
            checkbox.closest('.part-card').classList.add('selected');
        });
        this.updateCounts();
        this.showToast('All parts selected', 'info');
    }

    clearAllParts() {
        this.partCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.closest('.part-card').classList.remove('selected');
        });
        this.updateCounts();
        this.showToast('All parts cleared', 'info');
    }

    updateCounts() {
        const selectedParts = document.querySelectorAll('.part-checkbox:checked').length;
        const selectedProviders = document.querySelectorAll('.provider-checkbox:checked').length;
        
        if (this.selectedCountSpan) {
            this.selectedCountSpan.textContent = selectedParts;
        }
        
        if (this.providerCountSpan) {
            this.providerCountSpan.textContent = selectedProviders;
        }
        
        // Update dispatch button state
        if (this.dispatchBtn) {
            this.dispatchBtn.disabled = selectedParts === 0 || selectedProviders === 0;
            
            if (selectedParts > 0 && selectedProviders > 0) {
                this.dispatchBtn.classList.remove('disabled:bg-gray-400');
                this.dispatchBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
            } else {
                this.dispatchBtn.classList.add('disabled:bg-gray-400');
                this.dispatchBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            }
        }
    }

    updateProviderRecommendations() {
        // Highlight recommended provider combinations
        const selectedProviders = Array.from(document.querySelectorAll('.provider-checkbox:checked'))
            .map(cb => cb.name.replace('include_', ''));
        
        // Show recommendations based on selection
        if (selectedProviders.length === 1 && selectedProviders.includes('assessor')) {
            this.showToast('Consider adding external providers for comparison', 'info');
        } else if (selectedProviders.length >= 3) {
            this.showToast('Good provider mix for comprehensive quotes', 'success');
        }
    }

    handleFormSubmission(event) {
        event.preventDefault();
        
        const selectedParts = document.querySelectorAll('.part-checkbox:checked').length;
        const selectedProviders = document.querySelectorAll('.provider-checkbox:checked').length;
        
        if (selectedParts === 0) {
            this.showToast('Please select at least one part', 'error');
            return;
        }
        
        if (selectedProviders === 0) {
            this.showToast('Please select at least one provider', 'error');
            return;
        }
        
        this.showConfirmationModal(selectedParts, selectedProviders);
    }

    setupConfirmationModal() {
        const cancelBtn = document.getElementById('cancel-confirmation');
        const confirmBtn = document.getElementById('confirm-dispatch');
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideConfirmationModal());
        }
        
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirmDispatch());
        }
    }

    showConfirmationModal(partCount, providerCount) {
        const message = document.getElementById('confirmation-message');
        if (message) {
            message.textContent = `You are about to dispatch quote requests for ${partCount} parts to ${providerCount} provider types. This action cannot be undone.`;
        }
        
        if (this.confirmationModal) {
            this.confirmationModal.classList.remove('hidden');
            this.confirmationModal.classList.add('flex');
        }
    }

    hideConfirmationModal() {
        if (this.confirmationModal) {
            this.confirmationModal.classList.add('hidden');
            this.confirmationModal.classList.remove('flex');
        }
    }

    async confirmDispatch() {
        this.hideConfirmationModal();
        this.showLoadingOverlay();
        
        try {
            const formData = new FormData(this.form);
            
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            
            const data = await response.json();
            
            this.hideLoadingOverlay();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                
                // Reset form
                this.resetForm();
                
                // Refresh request history
                await this.refreshRequestHistory();
                
                // Refresh page after delay to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showToast(data.message, 'error');
            }
        } catch (error) {
            this.hideLoadingOverlay();
            this.showToast('An error occurred while dispatching quote requests.', 'error');
            console.error('Error:', error);
        }
    }

    resetForm() {
        // Clear all selections
        this.providerCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.closest('.provider-card').classList.remove('selected');
        });
        
        this.partCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.closest('.part-card').classList.remove('selected');
        });
        
        this.updateCounts();
    }

    showLoadingOverlay() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hideLoadingOverlay() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    setupCancelRequestButtons() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('cancel-request-btn')) {
                this.handleCancelRequest(e.target);
            }
        });
    }

    async handleCancelRequest(button) {
        const requestId = button.dataset.requestId;
        
        if (!confirm(`Are you sure you want to cancel quote request ${requestId}?`)) {
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('action', 'cancel_request');
            formData.append('request_id', requestId);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(data.message, 'success');
                await this.refreshRequestHistory();
            } else {
                this.showToast(data.message, 'error');
            }
        } catch (error) {
            this.showToast('An error occurred while cancelling the request.', 'error');
            console.error('Error:', error);
        }
    }

    async refreshRequestHistory() {
        try {
            const response = await fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newHistory = doc.getElementById('request-history');
            
            if (newHistory) {
                const currentHistory = document.getElementById('request-history');
                if (currentHistory) {
                    currentHistory.innerHTML = newHistory.innerHTML;
                }
            }
        } catch (error) {
            console.error('Error refreshing request history:', error);
        }
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.refreshRequestHistory();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg z-50 text-white transition-all duration-300 transform translate-x-full`;
        
        // Set background color based on type
        switch (type) {
            case 'success':
                toast.classList.add('bg-green-500');
                break;
            case 'error':
                toast.classList.add('bg-red-500');
                break;
            case 'warning':
                toast.classList.add('bg-yellow-500');
                break;
            default:
                toast.classList.add('bg-blue-500');
        }
        
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }

    // Cleanup method
    destroy() {
        this.stopAutoRefresh();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.quoteRequestManager = new QuoteRequestManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.quoteRequestManager) {
        window.quoteRequestManager.destroy();
    }
});