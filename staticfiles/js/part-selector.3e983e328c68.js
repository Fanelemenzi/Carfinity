/**
 * PartSelector - JavaScript component for managing part selection in maintenance records
 */
class PartSelector {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.selectedParts = new Map();
        this.searchTimeout = null;
        this.isSearching = false;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.searchInput = document.getElementById('part-search');
        this.searchResults = document.getElementById('search-results');
        this.searchLoading = document.getElementById('search-loading');
        
        // Add debug logging
        console.log('Initializing elements:', {
            searchInput: !!this.searchInput,
            searchResults: !!this.searchResults,
            searchLoading: !!this.searchLoading
        });
        
        this.selectedPartsBody = document.getElementById('selected-parts-body');
        this.noPartsRow = document.getElementById('no-parts-row');
        this.totalCostElement = document.getElementById('total-cost');
        this.partsCountElement = document.getElementById('parts-count');
        this.costBreakdown = document.getElementById('cost-breakdown');
        this.costBreakdownItems = document.getElementById('cost-breakdown-items');
        this.selectedPartsData = document.getElementById('selected-parts-data');
        this.partErrors = document.getElementById('part-errors');
        this.partErrorList = document.getElementById('part-error-list');
        this.partSuccess = document.getElementById('part-success');
        this.partSuccessMessage = document.getElementById('part-success-message');
    }
    
    bindEvents() {
        // Search input events
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.trim()) {
                this.showSearchResults();
            }
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideSearchResults();
            }
        });
    }
    
    handleSearch(query) {
        clearTimeout(this.searchTimeout);
        
        if (query.trim().length < 2) {
            this.hideSearchResults();
            return;
        }
        
        this.searchTimeout = setTimeout(() => {
            this.searchParts(query.trim());
        }, 300);
    }
    
    async searchParts(query) {
        if (this.isSearching) return;
        
        this.isSearching = true;
        this.showLoading();
        
        try {
            const response = await fetch(`/api/parts/search/?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.displaySearchResults(data.results || []);
            
        } catch (error) {
            console.error('Error searching parts:', error);
            this.showError('Failed to search parts. Please try again.');
        } finally {
            this.isSearching = false;
            // Force hide loading with a small delay to ensure it's hidden
            setTimeout(() => {
                this.hideLoading();
            }, 100);
        }
    }
    
    displaySearchResults(parts) {
        this.searchResults.innerHTML = '';
        
        if (parts.length === 0) {
            this.searchResults.innerHTML = `
                <div class="px-4 py-3 text-gray-500 text-center">
                    No parts found matching your search
                </div>
            `;
        } else {
            parts.forEach(part => {
                const resultItem = this.createSearchResultItem(part);
                this.searchResults.appendChild(resultItem);
            });
        }
        
        this.showSearchResults();
    }
    
    createSearchResultItem(part) {
        const div = document.createElement('div');
        div.className = 'search-result-item px-4 py-3 cursor-pointer border-b border-gray-100 last:border-b-0';
        
        const stockStatus = part.stock_quantity <= part.minimum_stock_level ? 'Low Stock' : 'In Stock';
        const stockClass = part.stock_quantity <= part.minimum_stock_level ? 'text-orange-600' : 'text-green-600';
        
        div.innerHTML = `
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <div class="font-medium text-gray-900">${this.escapeHtml(part.name)}</div>
                    <div class="text-sm text-gray-600">Part #: ${this.escapeHtml(part.part_number)}</div>
                    <div class="text-sm ${stockClass}">${stockStatus} (${part.stock_quantity} available)</div>
                </div>
                <div class="text-right ml-4">
                    <div class="font-medium text-gray-900">$${part.cost.toFixed(2)}</div>
                    <div class="text-sm text-gray-600">per unit</div>
                </div>
            </div>
        `;
        
        div.addEventListener('click', () => {
            this.selectPart(part);
            this.hideSearchResults();
            this.searchInput.value = '';
        });
        
        return div;
    }
    
    selectPart(part) {
        if (this.selectedParts.has(part.id)) {
            this.showError(`Part "${part.name}" is already selected`);
            return;
        }
        
        const partData = {
            ...part,
            quantity: 1,
            totalCost: part.cost
        };
        
        this.selectedParts.set(part.id, partData);
        this.addPartToTable(partData);
        this.updateCostSummary();
        this.updateHiddenInput();
        this.hideNoPartsRow();
        this.clearErrors();
        
        this.showSuccess(`Added "${part.name}" to selected parts`);
    }
    
    addPartToTable(part) {
        const row = document.createElement('tr');
        row.className = 'part-row-enter';
        row.id = `part-row-${part.id}`;
        
        row.innerHTML = `
            <td class="px-4 py-3">
                <div class="font-medium text-gray-900">${this.escapeHtml(part.name)}</div>
                <div class="text-sm text-gray-600">${this.escapeHtml(part.category || 'General')}</div>
            </td>
            <td class="px-4 py-3 text-gray-900">${this.escapeHtml(part.part_number)}</td>
            <td class="px-4 py-3 text-gray-900">$${part.cost.toFixed(2)}</td>
            <td class="px-4 py-3">
                <input 
                    type="number" 
                    min="1" 
                    max="${part.stock_quantity}"
                    value="${part.quantity}"
                    class="quantity-input w-20 px-2 py-1 border border-gray-300 rounded text-center"
                    data-part-id="${part.id}"
                />
                <div class="text-xs text-gray-500 mt-1">${part.stock_quantity} available</div>
            </td>
            <td class="px-4 py-3">
                <span class="font-medium text-gray-900" id="total-${part.id}">$${part.totalCost.toFixed(2)}</span>
            </td>
            <td class="px-4 py-3">
                <button 
                    type="button" 
                    class="btn-remove bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                    data-part-id="${part.id}"
                >
                    Remove
                </button>
            </td>
        `;
        
        this.selectedPartsBody.appendChild(row);
        
        // Bind events for the new row
        const quantityInput = row.querySelector('.quantity-input');
        const removeButton = row.querySelector('.btn-remove');
        
        quantityInput.addEventListener('change', (e) => {
            this.updatePartQuantity(part.id, parseInt(e.target.value));
        });
        
        removeButton.addEventListener('click', () => {
            this.removePart(part.id);
        });
    }
    
    updatePartQuantity(partId, newQuantity) {
        const part = this.selectedParts.get(partId);
        if (!part) return;
        
        // Validate quantity
        if (newQuantity < 1) {
            this.showError('Quantity must be at least 1');
            document.querySelector(`input[data-part-id="${partId}"]`).value = part.quantity;
            return;
        }
        
        if (newQuantity > part.stock_quantity) {
            this.showError(`Only ${part.stock_quantity} units available for "${part.name}"`);
            document.querySelector(`input[data-part-id="${partId}"]`).value = part.quantity;
            return;
        }
        
        // Update part data
        part.quantity = newQuantity;
        part.totalCost = part.cost * newQuantity;
        
        // Update display
        document.getElementById(`total-${partId}`).textContent = `$${part.totalCost.toFixed(2)}`;
        
        this.updateCostSummary();
        this.updateHiddenInput();
        this.clearErrors();
    }
    
    removePart(partId) {
        const part = this.selectedParts.get(partId);
        if (!part) return;
        
        // Remove from selected parts
        this.selectedParts.delete(partId);
        
        // Remove from table with animation
        const row = document.getElementById(`part-row-${partId}`);
        if (row) {
            row.classList.add('part-row-exit');
            setTimeout(() => {
                row.remove();
                if (this.selectedParts.size === 0) {
                    this.showNoPartsRow();
                }
            }, 300);
        }
        
        this.updateCostSummary();
        this.updateHiddenInput();
        
        this.showSuccess(`Removed "${part.name}" from selected parts`);
    }
    
    updateCostSummary() {
        let totalCost = 0;
        const breakdownItems = [];
        
        this.selectedParts.forEach(part => {
            totalCost += part.totalCost;
            breakdownItems.push({
                name: part.name,
                quantity: part.quantity,
                unitCost: part.cost,
                totalCost: part.totalCost
            });
        });
        
        // Update total cost with animation
        this.totalCostElement.classList.add('cost-update');
        this.totalCostElement.textContent = `$${totalCost.toFixed(2)}`;
        setTimeout(() => {
            this.totalCostElement.classList.remove('cost-update');
        }, 500);
        
        // Update parts count
        this.partsCountElement.textContent = this.selectedParts.size;
        
        // Update cost breakdown
        if (breakdownItems.length > 0) {
            this.costBreakdownItems.innerHTML = breakdownItems.map(item => `
                <div class="flex justify-between text-sm">
                    <span>${this.escapeHtml(item.name)} (${item.quantity}x)</span>
                    <span>$${item.totalCost.toFixed(2)}</span>
                </div>
            `).join('');
            this.costBreakdown.classList.remove('hidden');
        } else {
            this.costBreakdown.classList.add('hidden');
        }
    }
    
    updateHiddenInput() {
        const partsData = Array.from(this.selectedParts.values()).map(part => ({
            id: part.id,
            quantity: part.quantity,
            unit_cost: part.cost
        }));
        
        this.selectedPartsData.value = JSON.stringify(partsData);
    }
    
    showSearchResults() {
        this.searchResults.classList.remove('hidden');
    }
    
    hideSearchResults() {
        this.searchResults.classList.add('hidden');
    }
    
    showLoading() {
        console.log('showLoading called, searchLoading element:', this.searchLoading);
        if (this.searchLoading) {
            this.searchLoading.classList.remove('hidden');
            console.log('Loading shown');
        } else {
            console.error('searchLoading element not found!');
        }
    }
    
    hideLoading() {
        console.log('hideLoading called, searchLoading element:', this.searchLoading);
        if (this.searchLoading) {
            this.searchLoading.classList.add('hidden');
            console.log('Loading hidden');
        } else {
            console.error('searchLoading element not found!');
        }
    }
    
    hideNoPartsRow() {
        this.noPartsRow.classList.add('hidden');
    }
    
    showNoPartsRow() {
        this.noPartsRow.classList.remove('hidden');
    }
    
    showError(message) {
        this.partErrorList.innerHTML = `<p>${this.escapeHtml(message)}</p>`;
        this.partErrors.classList.remove('hidden');
        this.partSuccess.classList.add('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.clearErrors();
        }, 5000);
    }
    
    showSuccess(message) {
        this.partSuccessMessage.textContent = message;
        this.partSuccess.classList.remove('hidden');
        this.partErrors.classList.add('hidden');
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.partSuccess.classList.add('hidden');
        }, 3000);
    }
    
    clearErrors() {
        this.partErrors.classList.add('hidden');
        this.partErrorList.innerHTML = '';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public method to validate selected parts before form submission
    validateSelection() {
        const errors = [];
        
        this.selectedParts.forEach(part => {
            if (part.quantity > part.stock_quantity) {
                errors.push(`${part.name}: Requested quantity (${part.quantity}) exceeds available stock (${part.stock_quantity})`);
            }
            if (part.quantity < 1) {
                errors.push(`${part.name}: Quantity must be at least 1`);
            }
        });
        
        if (errors.length > 0) {
            this.partErrorList.innerHTML = errors.map(error => `<p>${this.escapeHtml(error)}</p>`).join('');
            this.partErrors.classList.remove('hidden');
            return false;
        }
        
        return true;
    }
    
    // Public method to get selected parts data
    getSelectedParts() {
        return Array.from(this.selectedParts.values());
    }
    
    // Public method to clear all selected parts
    clearSelection() {
        this.selectedParts.clear();
        this.selectedPartsBody.innerHTML = '';
        this.showNoPartsRow();
        this.updateCostSummary();
        this.updateHiddenInput();
        this.clearErrors();
    }
}

// Initialize part selector when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('part-search')) {
        window.partSelector = new PartSelector('part-selection-container');
        
        // Add form validation before submission
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!window.partSelector.validateSelection()) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    }
});