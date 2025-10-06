/**
 * Assessment Dashboard Filtering and Search Functionality
 * Provides client-side filtering, searching, and sorting for the assessment table
 */

class AssessmentDashboardFilters {
    constructor() {
        this.tableBody = document.getElementById('claimsTableBody');
        this.searchInput = document.getElementById('globalSearch');
        this.statusFilter = document.getElementById('statusFilter');
        this.priorityFilter = document.getElementById('priorityFilter');
        this.dateFromInput = document.getElementById('dateFrom');
        this.dateToInput = document.getElementById('dateTo');
        this.valueFromInput = document.getElementById('valueFrom');
        this.valueToInput = document.getElementById('valueTo');
        this.clearFiltersBtn = document.getElementById('clearFilters');
        this.sortableHeaders = document.querySelectorAll('.sortable');
        
        this.originalRows = [];
        this.currentSort = { column: null, direction: 'asc' };
        
        this.init();
    }
    
    init() {
        // Store original table rows
        this.storeOriginalRows();
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Apply any existing filters from URL parameters
        this.applyUrlFilters();
        
        console.log('Assessment Dashboard Filters initialized');
    }
    
    storeOriginalRows() {
        if (this.tableBody) {
            this.originalRows = Array.from(this.tableBody.querySelectorAll('tr')).map(row => ({
                element: row.cloneNode(true),
                data: this.extractRowData(row)
            }));
        }
    }
    
    extractRowData(row) {
        return {
            claimId: row.dataset.claimId || '',
            status: row.dataset.status || '',
            priority: row.dataset.priority || '',
            vehicle: row.dataset.vehicle || '',
            value: parseFloat(row.dataset.value) || 0,
            date: row.dataset.date || '',
            customer: row.dataset.customer || '',
            vin: row.dataset.vin || '',
            text: row.textContent.toLowerCase()
        };
    }
    
    bindEventListeners() {
        // Search input
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.debounce(() => {
                this.applyFilters();
            }, 300));
        }
        
        // Status filter
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }
        
        // Priority filter
        if (this.priorityFilter) {
            this.priorityFilter.addEventListener('change', () => {
                this.applyFilters();
            });
        }
        
        // Date range filters
        if (this.dateFromInput) {
            this.dateFromInput.addEventListener('change', () => {
                this.applyFilters();
            });
        }
        
        if (this.dateToInput) {
            this.dateToInput.addEventListener('change', () => {
                this.applyFilters();
            });
        }
        
        // Value range filters
        if (this.valueFromInput) {
            this.valueFromInput.addEventListener('input', this.debounce(() => {
                this.applyFilters();
            }, 500));
        }
        
        if (this.valueToInput) {
            this.valueToInput.addEventListener('input', this.debounce(() => {
                this.applyFilters();
            }, 500));
        }
        
        // Clear filters button
        if (this.clearFiltersBtn) {
            this.clearFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
        
        // Sortable headers
        this.sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortColumn = header.dataset.sort;
                this.sortTable(sortColumn);
            });
        });
        
        // Date range filter (if implemented)
        this.bindDateRangeFilter();
        
        // Value range filter (if implemented)
        this.bindValueRangeFilter();
    }
    
    applyUrlFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Apply search filter
        const searchQuery = urlParams.get('search');
        if (searchQuery && this.searchInput) {
            this.searchInput.value = searchQuery;
        }
        
        // Apply status filter
        const statusFilter = urlParams.get('status');
        if (statusFilter && this.statusFilter) {
            this.statusFilter.value = statusFilter;
        }
        
        // Apply filters if any exist
        if (searchQuery || statusFilter) {
            this.applyFilters();
        }
    }
    
    applyFilters() {
        const searchQuery = this.searchInput ? this.searchInput.value.toLowerCase().trim() : '';
        const statusFilter = this.statusFilter ? this.statusFilter.value : '';
        const priorityFilter = this.priorityFilter ? this.priorityFilter.value : '';
        const dateFrom = this.dateFromInput ? this.dateFromInput.value : '';
        const dateTo = this.dateToInput ? this.dateToInput.value : '';
        const valueFrom = this.valueFromInput ? parseFloat(this.valueFromInput.value) || 0 : 0;
        const valueTo = this.valueToInput ? parseFloat(this.valueToInput.value) || Infinity : Infinity;
        
        let filteredRows = this.originalRows.filter(rowData => {
            const data = rowData.data;
            
            // Search filter
            if (searchQuery && !this.matchesSearch(data, searchQuery)) {
                return false;
            }
            
            // Status filter
            if (statusFilter && data.status.toLowerCase() !== statusFilter.toLowerCase()) {
                return false;
            }
            
            // Priority filter
            if (priorityFilter && data.priority !== priorityFilter) {
                return false;
            }
            
            // Date range filter
            if (dateFrom || dateTo) {
                const assessmentDate = new Date(data.date);
                if (dateFrom && assessmentDate < new Date(dateFrom)) {
                    return false;
                }
                if (dateTo && assessmentDate > new Date(dateTo)) {
                    return false;
                }
            }
            
            // Value range filter
            if (valueFrom > 0 && data.value < valueFrom) {
                return false;
            }
            if (valueTo < Infinity && data.value > valueTo) {
                return false;
            }
            
            return true;
        });
        
        // Apply current sort if any
        if (this.currentSort.column) {
            filteredRows = this.sortRows(filteredRows, this.currentSort.column, this.currentSort.direction);
        }
        
        this.updateTable(filteredRows);
        this.updateFilterStats(filteredRows.length);
        this.updateUrlParams();
    }
    
    matchesSearch(data, query) {
        const searchFields = [
            data.claimId,
            data.vehicle,
            data.customer,
            data.vin,
            data.text
        ];
        
        return searchFields.some(field => 
            field.toLowerCase().includes(query)
        );
    }
    
    sortTable(column) {
        // Toggle sort direction
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }
        
        // Update sort icons
        this.updateSortIcons(column, this.currentSort.direction);
        
        // Apply sort to current filtered results
        this.applyFilters();
    }
    
    sortRows(rows, column, direction) {
        return rows.sort((a, b) => {
            let aVal, bVal;
            
            switch (column) {
                case 'priority':
                    aVal = this.getPriorityValue(a.data.priority);
                    bVal = this.getPriorityValue(b.data.priority);
                    break;
                case 'id':
                    aVal = a.data.claimId;
                    bVal = b.data.claimId;
                    break;
                case 'vehicle':
                    aVal = a.data.vehicle;
                    bVal = b.data.vehicle;
                    break;
                case 'value':
                    aVal = a.data.value;
                    bVal = b.data.value;
                    break;
                case 'status':
                    aVal = a.data.status;
                    bVal = b.data.status;
                    break;
                case 'date':
                    aVal = new Date(a.data.date);
                    bVal = new Date(b.data.date);
                    break;
                default:
                    aVal = a.data.text;
                    bVal = b.data.text;
            }
            
            let comparison = 0;
            if (aVal > bVal) comparison = 1;
            if (aVal < bVal) comparison = -1;
            
            return direction === 'desc' ? -comparison : comparison;
        });
    }
    
    getPriorityValue(priority) {
        const priorityMap = {
            'URGENT': 3,
            'HIGH': 2,
            'NORMAL': 1,
            'LOW': 0
        };
        return priorityMap[priority] || 0;
    }
    
    updateSortIcons(activeColumn, direction) {
        this.sortableHeaders.forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (!icon) return;
            
            if (header.dataset.sort === activeColumn) {
                icon.className = `sort-icon fas fa-sort-${direction === 'asc' ? 'up' : 'down'} ml-1`;
                header.classList.add('bg-gray-100');
            } else {
                icon.className = 'sort-icon fas fa-sort ml-1';
                header.classList.remove('bg-gray-100');
            }
        });
    }
    
    updateTable(filteredRows) {
        if (!this.tableBody) return;
        
        // Clear current table
        this.tableBody.innerHTML = '';
        
        if (filteredRows.length === 0) {
            // Show no results message
            this.showNoResultsMessage();
        } else {
            // Add filtered rows
            filteredRows.forEach(rowData => {
                const newRow = rowData.element.cloneNode(true);
                // Re-bind click events
                this.bindRowEvents(newRow);
                this.tableBody.appendChild(newRow);
            });
        }
    }
    
    showNoResultsMessage() {
        const noResultsRow = document.createElement('tr');
        noResultsRow.innerHTML = `
            <td colspan="6" class="px-6 py-12 text-center">
                <div class="text-gray-500">
                    <i class="fas fa-search text-4xl mb-4"></i>
                    <p class="text-lg font-medium">No assessments found</p>
                    <p class="text-sm">Try adjusting your search criteria or filters.</p>
                    <button onclick="assessmentFilters.clearAllFilters()" class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                        Clear Filters
                    </button>
                </div>
            </td>
        `;
        this.tableBody.appendChild(noResultsRow);
    }
    
    bindRowEvents(row) {
        // Re-bind click event for viewing claim details
        row.addEventListener('click', () => {
            const claimId = row.dataset.claimId;
            if (claimId && typeof viewClaim === 'function') {
                viewClaim(claimId);
            }
        });
        
        // Re-bind hover effects
        row.classList.add('hover:bg-gray-50', 'cursor-pointer', 'transition-all', 'duration-200');
    }
    
    updateFilterStats(filteredCount) {
        // Update any filter statistics display
        const totalCount = this.originalRows.length;
        
        // Update table header with count if element exists
        const tableHeader = document.querySelector('.claims-table-header');
        if (tableHeader) {
            let countText = `Showing ${filteredCount} of ${totalCount} assessments`;
            if (filteredCount !== totalCount) {
                countText += ' (filtered)';
            }
            
            let countElement = tableHeader.querySelector('.filter-count');
            if (!countElement) {
                countElement = document.createElement('span');
                countElement.className = 'filter-count text-sm text-gray-500 ml-4';
                tableHeader.appendChild(countElement);
            }
            countElement.textContent = countText;
        }
    }
    
    clearAllFilters() {
        // Clear search input
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        
        // Clear status filter
        if (this.statusFilter) {
            this.statusFilter.value = '';
        }
        
        // Clear priority filter
        if (this.priorityFilter) {
            this.priorityFilter.value = '';
        }
        
        // Clear date range filters
        if (this.dateFromInput) {
            this.dateFromInput.value = '';
        }
        if (this.dateToInput) {
            this.dateToInput.value = '';
        }
        
        // Clear value range filters
        if (this.valueFromInput) {
            this.valueFromInput.value = '';
        }
        if (this.valueToInput) {
            this.valueToInput.value = '';
        }
        
        // Reset sort
        this.currentSort = { column: null, direction: 'asc' };
        this.updateSortIcons('', 'asc');
        
        // Apply filters (which will show all results)
        this.applyFilters();
        
        console.log('All filters cleared');
    }
    
    bindDateRangeFilter() {
        // Implementation for date range filtering
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        
        if (dateFromInput && dateToInput) {
            [dateFromInput, dateToInput].forEach(input => {
                input.addEventListener('change', () => {
                    this.applyFilters();
                });
            });
        }
    }
    
    bindValueRangeFilter() {
        // Implementation for value range filtering
        const valueFromInput = document.getElementById('valueFrom');
        const valueToInput = document.getElementById('valueTo');
        
        if (valueFromInput && valueToInput) {
            [valueFromInput, valueToInput].forEach(input => {
                input.addEventListener('input', this.debounce(() => {
                    this.applyFilters();
                }, 500));
            });
        }
    }
    
    clearDateRangeFilter() {
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        
        if (dateFromInput) dateFromInput.value = '';
        if (dateToInput) dateToInput.value = '';
    }
    
    clearValueRangeFilter() {
        const valueFromInput = document.getElementById('valueFrom');
        const valueToInput = document.getElementById('valueTo');
        
        if (valueFromInput) valueFromInput.value = '';
        if (valueToInput) valueToInput.value = '';
    }
    
    updateUrlParams() {
        const url = new URL(window.location);
        const searchQuery = this.searchInput ? this.searchInput.value : '';
        const statusFilter = this.statusFilter ? this.statusFilter.value : '';
        
        if (searchQuery) {
            url.searchParams.set('search', searchQuery);
        } else {
            url.searchParams.delete('search');
        }
        
        if (statusFilter) {
            url.searchParams.set('status', statusFilter);
        } else {
            url.searchParams.delete('status');
        }
        
        // Update URL without page reload
        window.history.replaceState({}, '', url);
    }
    
    // Utility function for debouncing
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Public method to add custom filters
    addCustomFilter(name, filterFunction) {
        this.customFilters = this.customFilters || {};
        this.customFilters[name] = filterFunction;
    }
    
    // Public method to remove custom filters
    removeCustomFilter(name) {
        if (this.customFilters && this.customFilters[name]) {
            delete this.customFilters[name];
        }
    }
}

// Global function for viewing claim details (called from table rows)
function viewClaim(claimId) {
    if (claimId) {
        // Navigate to assessment detail page
        window.location.href = `/insurance/assessment/${claimId}/`;
    }
}

// Initialize the filters when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize assessment dashboard filters
    window.assessmentFilters = new AssessmentDashboardFilters();
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AssessmentDashboardFilters;
}