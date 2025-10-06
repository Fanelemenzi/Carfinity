/**
 * Claims Table Interactivity JavaScript
 * Handles interactive elements for claims table (sorting, filtering, row selection)
 * Implements popup modal functionality and smooth tab switching
 */

// Global state for claims table
const ClaimsTableState = {
    currentSort: { column: null, direction: 'asc' },
    activeFilters: {},
    selectedRows: new Set(),
    currentPage: 1,
    itemsPerPage: 10,
    searchQuery: '',
    isLoading: false
};

// Sample claims data for demonstration
const claimsData = {
    'CLM-2024-001': {
        id: 'CLM-2024-001',
        customer: 'John Smith',
        vehicle: '2020 Toyota Camry LE',
        status: 'active',
        date: '2024-01-15',
        priority: 'high',
        vin: '1HGBH41JXMN109186',
        mileage: '45,230',
        damages: ['Front bumper damage', 'Headlight replacement needed'],
        severity: 'Moderate',
        policyNumber: 'POL-789456123',
        coverageType: 'Comprehensive',
        deductible: '£500',
        location: 'Manchester, UK',
        estimatedCost: '£3,250',
        coverage: '£15,000',
        settlement: '£2,750'
    },
    'CLM-2024-002': {
        id: 'CLM-2024-002',
        customer: 'Sarah Johnson',
        vehicle: '2019 Honda Civic Sport',
        status: 'pending',
        date: '2024-01-14',
        priority: 'medium',
        vin: '2HGFC2F59KH123456',
        mileage: '32,150',
        damages: ['Rear panel dent', 'Taillight damage'],
        severity: 'Minor',
        policyNumber: 'POL-456789012',
        coverageType: 'Collision',
        deductible: '£250',
        location: 'London, UK',
        estimatedCost: '£1,850',
        coverage: '£10,000',
        settlement: '£1,600'
    }
};

// Initialize claims table functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeClaimsTable();
});

/**
 * Main initialization function for claims table
 */
function initializeClaimsTable() {
    setupTableSorting();
    setupTableFiltering();
    setupSearchFunctionality();
    setupDirectNavigation();
    setupTableRowClickHandlers();
    console.log('Claims table initialized successfully');
}

/**
 * Setup table sorting functionality
 */
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable');

    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const column = this.getAttribute('data-sort');
            handleSort(column);
        });
    });
}

/**
 * Handle sorting logic
 */
function handleSort(column) {
    if (ClaimsTableState.currentSort.column === column) {
        ClaimsTableState.currentSort.direction =
            ClaimsTableState.currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        ClaimsTableState.currentSort.column = column;
        ClaimsTableState.currentSort.direction = 'asc';
    }
    applySorting();
    updateSortIndicators();
}

/**
 * Apply sorting to table rows
 */
function applySorting() {
    const tbody = document.getElementById('claimsTableBody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    const { column, direction } = ClaimsTableState.currentSort;

    if (!column) return;

    rows.sort((a, b) => {
        const aValue = a.getAttribute(`data-${column}`) || '';
        const bValue = b.getAttribute(`data-${column}`) || '';

        let comparison = 0;
        if (column === 'date') {
            comparison = new Date(aValue) - new Date(bValue);
        } else if (column === 'priority') {
            const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
            comparison = (priorityOrder[aValue] || 0) - (priorityOrder[bValue] || 0);
        } else {
            comparison = aValue.localeCompare(bValue);
        }

        return direction === 'desc' ? -comparison : comparison;
    });

    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Update sort indicators in table headers
 */
function updateSortIndicators() {
    const sortableHeaders = document.querySelectorAll('.sortable');

    sortableHeaders.forEach(header => {
        const column = header.getAttribute('data-sort');
        const icon = header.querySelector('.sort-icon');

        if (icon) {
            icon.className = 'sort-icon fas ml-1';

            if (column === ClaimsTableState.currentSort.column) {
                icon.classList.add(
                    ClaimsTableState.currentSort.direction === 'asc' ? 'fa-sort-up' : 'fa-sort-down'
                );
                header.classList.add('text-primary');
            } else {
                icon.classList.add('fa-sort');
                header.classList.remove('text-primary');
            }
        }
    });
}

/**
 * Setup table filtering functionality
 */
function setupTableFiltering() {
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const dateFilter = document.getElementById('dateFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');

    [statusFilter, document.getElementById('statusFilterTablet'), document.getElementById('statusFilterMobile')].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function () {
                ClaimsTableState.activeFilters.status = this.value;
                applyFilters();
            });
        }
    });

    [priorityFilter, document.getElementById('priorityFilterTablet'), document.getElementById('priorityFilterMobile')].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function () {
                ClaimsTableState.activeFilters.priority = this.value;
                applyFilters();
            });
        }
    });

    [dateFilter, document.getElementById('dateFilterTablet'), document.getElementById('dateFilterMobile')].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function () {
                ClaimsTableState.activeFilters.date = this.value;
                applyFilters();
            });
        }
    });

    [clearFiltersBtn, document.getElementById('clearFiltersTablet'), document.getElementById('clearFiltersMobile')].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', clearAllFilters);
        }
    });
}

/**
 * Apply filters to table rows
 */
function applyFilters() {
    const rows = document.querySelectorAll('#claimsTableBody tr, .mobile-claim-card');
    let visibleCount = 0;

    rows.forEach(row => {
        let shouldShow = true;

        Object.entries(ClaimsTableState.activeFilters).forEach(([filterType, filterValue]) => {
            if (filterValue && filterValue !== '') {
                const rowValue = row.getAttribute(`data-${filterType}`);

                if (filterType === 'date' && filterValue) {
                    const rowDate = new Date(rowValue);
                    const filterDate = new Date(filterValue);
                    if (rowDate < filterDate) {
                        shouldShow = false;
                    }
                } else if (rowValue !== filterValue) {
                    shouldShow = false;
                }
            }
        });

        if (ClaimsTableState.searchQuery) {
            const searchableText = row.textContent.toLowerCase();
            if (!searchableText.includes(ClaimsTableState.searchQuery.toLowerCase())) {
                shouldShow = false;
            }
        }

        row.style.display = shouldShow ? '' : 'none';
        if (shouldShow) visibleCount++;
    });

    updateFilterCount(visibleCount);
}

/**
 * Clear all active filters
 */
function clearAllFilters() {
    ClaimsTableState.activeFilters = {};
    ClaimsTableState.searchQuery = '';

    const filterInputs = document.querySelectorAll('[id*="Filter"]');
    filterInputs.forEach(input => {
        input.value = '';
    });

    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.value = '';
    }

    applyFilters();
}

/**
 * Update filter count display
 */
function updateFilterCount(count) {
    const countElement = document.getElementById('filterCount');
    if (countElement) {
        countElement.textContent = `${count} claims shown`;
    }
}

/**
 * Setup search functionality
 */
function setupSearchFunctionality() {
    const searchInput = document.getElementById('globalSearch');

    if (searchInput) {
        let searchTimeout;

        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                ClaimsTableState.searchQuery = this.value;
                applyFilters();
            }, 300);
        });

        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                this.value = '';
                ClaimsTableState.searchQuery = '';
                applyFilters();
            }
        });
    }
}

/**
 * Setup direct navigation functionality (replaces modal popup)
 */
function setupDirectNavigation() {
    // Direct navigation is handled by viewClaim function
    console.log('Direct navigation setup completed');
}

/**
 * Direct claim navigation (replaces modal creation)
 */
function navigateToClaimDetail(claimId) {
    console.log('Navigating directly to claim:', claimId);
    window.location.href = `/insurance/assessments/${claimId}/`;
}

/**
 * Navigate directly to claim detail (replaces popup)
 */
function showClaimPopup(claimId) {
    console.log('Direct navigation to claim:', claimId);
    navigateToClaimDetail(claimId);
}

/**
 * Legacy function - no longer needed with direct navigation
 */
function closeClaimModal() {
    // No longer needed - direct navigation replaces modal
    console.log('closeClaimModal called but no longer needed with direct navigation');
}

/**
 * Get claim data from DOM if not in claimsData object
 */
function getClaimDataFromDOM(claimId) {
    const row = document.querySelector(`[data-claim-id="${claimId}"]`);
    if (!row) return null;

    return {
        id: claimId,
        customer: row.querySelector('.customer-name')?.textContent || 'Unknown',
        vehicle: row.querySelector('.vehicle-info')?.textContent || 'Unknown',
        status: row.getAttribute('data-status') || 'unknown',
        date: row.getAttribute('data-date') || '',
        priority: row.getAttribute('data-priority') || 'medium',
        vin: 'Not available',
        mileage: 'Not available',
        damages: ['Information not available'],
        severity: 'Unknown',
        policyNumber: 'Not available',
        coverageType: 'Not available',
        deductible: 'Not available',
        location: 'Not available',
        estimatedCost: 'Not available',
        coverage: 'Not available',
        settlement: 'Not available'
    };
}

/**
 * Generate claim modal content HTML
 */
function generateClaimModalContent(claim) {
    return `
        <div class="space-y-6">
            <!-- Vehicle Details Section -->
            <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
                    <i class="fas fa-car text-blue-600 mr-2"></i>
                    Vehicle Details
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="font-medium text-gray-700">Vehicle:</span>
                        <span class="ml-2 text-gray-900">${claim.vehicle}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">VIN:</span>
                        <span class="ml-2 text-gray-900">${claim.vin}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Mileage:</span>
                        <span class="ml-2 text-gray-900">${claim.mileage}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Location:</span>
                        <span class="ml-2 text-gray-900">${claim.location}</span>
                    </div>
                </div>
            </div>
            
            <!-- Visual Damages Section -->
            <div class="bg-red-50 rounded-lg p-4">
                <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
                    <i class="fas fa-exclamation-triangle text-red-600 mr-2"></i>
                    Visual Damages Overview
                </h4>
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">Severity:</span>
                        <span class="px-2 py-1 text-xs font-medium rounded-full ${getSeverityBadgeClass(claim.severity)}">
                            ${claim.severity}
                        </span>
                    </div>
                    <div>
                        <span class="text-sm font-medium text-gray-700">Damages:</span>
                        <ul class="mt-1 text-sm text-gray-900">
                            ${claim.damages.map(damage => `<li class="flex items-center"><i class="fas fa-dot-circle text-red-500 mr-2 text-xs"></i>${damage}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Policy Details Section -->
            <div class="bg-blue-50 rounded-lg p-4">
                <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
                    <i class="fas fa-file-contract text-blue-600 mr-2"></i>
                    Policy Details
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="font-medium text-gray-700">Policy Number:</span>
                        <span class="ml-2 text-gray-900">${claim.policyNumber}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Coverage Type:</span>
                        <span class="ml-2 text-gray-900">${claim.coverageType}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Deductible:</span>
                        <span class="ml-2 text-gray-900">${claim.deductible}</span>
                    </div>
                </div>
            </div>
            
            <!-- Financial Summary Section -->
            <div class="bg-green-50 rounded-lg p-4">
                <h4 class="text-md font-medium text-gray-900 mb-3 flex items-center">
                    <i class="fas fa-pound-sign text-green-600 mr-2"></i>
                    Financial Summary
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div class="text-center">
                        <div class="text-lg font-bold text-gray-900">${claim.estimatedCost}</div>
                        <div class="text-gray-600">Estimated Cost</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-gray-900">${claim.coverage}</div>
                        <div class="text-gray-600">Policy Coverage</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-green-600">${claim.settlement}</div>
                        <div class="text-gray-600">Settlement Amount</div>
                    </div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex justify-between items-center pt-4 border-t border-gray-200">
                <button type="button" class="modal-close px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
                    Close
                </button>
                <button type="button" onclick="viewFullDetail('${claim.id}')" class="px-4 py-2 text-sm font-medium text-white bg-primary border border-transparent rounded-md hover:bg-blue-700">
                    View Full Detail
                </button>
            </div>
        </div>
    `;
}

/**
 * Get severity badge CSS class
 */
function getSeverityBadgeClass(severity) {
    switch (severity.toLowerCase()) {
        case 'minor':
            return 'bg-green-100 text-green-800';
        case 'moderate':
            return 'bg-yellow-100 text-yellow-800';
        case 'severe':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

/**
 * Direct navigation to full detail view
 */
function viewFullDetail(claimId) {
    console.log('Navigating to full detail view for claim:', claimId);
    navigateToClaimDetail(claimId);
}

/**
 * Setup click handlers for direct navigation
 * Ensures claims navigate directly to detail page
 */
function setupTableRowClickHandlers() {
    document.addEventListener('click', function (e) {
        const row = e.target.closest('tr[data-claim-id]');
        if (row && !e.target.closest('button')) {
            const claimId = row.getAttribute('data-claim-id');
            if (claimId) {
                console.log('Row clicked for claim:', claimId);
                navigateToClaimDetail(claimId);
            }
        }

        const mobileCard = e.target.closest('.mobile-claim-card[data-claim-id]');
        if (mobileCard && !e.target.closest('button')) {
            const claimId = mobileCard.getAttribute('data-claim-id');
            if (claimId) {
                console.log('Mobile card clicked for claim:', claimId);
                navigateToClaimDetail(claimId);
            }
        }
    });
}

// Make navigation functions globally available
window.showClaimPopup = showClaimPopup;
window.navigateToClaimDetail = navigateToClaimDetail;