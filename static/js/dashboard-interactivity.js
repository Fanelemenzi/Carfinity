/**
 * Dashboard Interactivity JavaScript
 * Handles interactive elements for insurance dashboard components
 */

// Global state management
const DashboardState = {
    activeFilters: {},
    sortOrder: 'desc',
    sortField: 'date',
    currentPage: 1,
    itemsPerPage: 10,
    notifications: [],
    collapsedSections: new Set()
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Main initialization function
 */
function initializeDashboard() {
    initializeCollapsibleSections();
    initializeTabs();
    initializeModals();
    initializeDataFiltering();
    initializePagination();
    initializeFormValidation();
    initializeMobileNavigation();
    initializeNotifications();
    initializeInteractiveElements();
    initializeKeyboardNavigation();
}

/**
 * Collapsible Sections Management
 */
function initializeCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('[data-collapsible]');
    
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const targetId = this.getAttribute('data-collapsible');
            const targetElement = document.getElementById(targetId);
            const isCollapsed = DashboardState.collapsedSections.has(targetId);
            
            if (targetElement) {
                toggleSection(targetElement, !isCollapsed);
                
                if (isCollapsed) {
                    DashboardState.collapsedSections.delete(targetId);
                } else {
                    DashboardState.collapsedSections.add(targetId);
                }
                
                // Update icon
                const icon = this.querySelector('.collapse-icon');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down', isCollapsed);
                    icon.classList.toggle('fa-chevron-up', !isCollapsed);
                }
            }
        });
    });
}

function toggleSection(element, show) {
    if (show) {
        element.style.maxHeight = element.scrollHeight + 'px';
        element.classList.remove('collapsed');
        element.setAttribute('aria-expanded', 'true');
    } else {
        element.style.maxHeight = '0';
        element.classList.add('collapsed');
        element.setAttribute('aria-expanded', 'false');
    }
}

/**
 * Tab Management
 */
function initializeTabs() {
    const tabButtons = document.querySelectorAll('[data-tab]');
    const tabPanels = document.querySelectorAll('[data-tab-panel]');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and panels
            tabButtons.forEach(btn => btn.classList.remove('active', 'text-primary', 'border-primary'));
            tabPanels.forEach(panel => panel.classList.add('hidden'));
            
            // Add active class to clicked tab
            this.classList.add('active', 'text-primary', 'border-primary');
            
            // Show corresponding panel
            const targetPanel = document.querySelector(`[data-tab-panel="${targetTab}"]`);
            if (targetPanel) {
                targetPanel.classList.remove('hidden');
            }
            
            // Update ARIA attributes
            tabButtons.forEach(btn => btn.setAttribute('aria-selected', 'false'));
            this.setAttribute('aria-selected', 'true');
        });
    });
}

/**
 * Modal Management
 */
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalCloses = document.querySelectorAll('[data-modal-close]');
    const modalOverlays = document.querySelectorAll('.modal-overlay');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });
    
    modalCloses.forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    modalOverlays.forEach(overlay => {
        overlay.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal:not(.hidden)');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus first focusable element
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

/**
 * Data Filtering and Sorting
 */
function initializeDataFiltering() {
    const filterInputs = document.querySelectorAll('[data-filter]');
    const sortButtons = document.querySelectorAll('[data-sort]');
    const searchInput = document.getElementById('globalSearch');
    
    filterInputs.forEach(input => {
        input.addEventListener('change', function() {
            const filterType = this.getAttribute('data-filter');
            const filterValue = this.value;
            
            DashboardState.activeFilters[filterType] = filterValue;
            applyFilters();
        });
    });
    
    sortButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sortField = this.getAttribute('data-sort');
            
            if (DashboardState.sortField === sortField) {
                DashboardState.sortOrder = DashboardState.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                DashboardState.sortField = sortField;
                DashboardState.sortOrder = 'asc';
            }
            
            applySorting();
            updateSortIndicators();
        });
    });
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300);
        });
    }
}

function applyFilters() {
    const tableRows = document.querySelectorAll('[data-filterable]');
    
    tableRows.forEach(row => {
        let shouldShow = true;
        
        Object.entries(DashboardState.activeFilters).forEach(([filterType, filterValue]) => {
            if (filterValue && filterValue !== 'all') {
                const cellValue = row.getAttribute(`data-${filterType}`);
                if (cellValue !== filterValue) {
                    shouldShow = false;
                }
            }
        });
        
        row.style.display = shouldShow ? '' : 'none';
    });
    
    updateFilterCounts();
}

function applySorting() {
    const container = document.querySelector('[data-sortable-container]');
    if (!container) return;
    
    const items = Array.from(container.querySelectorAll('[data-sortable]'));
    
    items.sort((a, b) => {
        const aValue = a.getAttribute(`data-${DashboardState.sortField}`);
        const bValue = b.getAttribute(`data-${DashboardState.sortField}`);
        
        let comparison = 0;
        
        // Handle different data types
        if (DashboardState.sortField === 'date') {
            const aDate = new Date(aValue);
            const bDate = new Date(bValue);
            comparison = aDate - bDate;
        } else if (DashboardState.sortField === 'value' || DashboardState.sortField === 'cost') {
            const aNum = parseFloat(aValue.replace(/[£$,]/g, '')) || 0;
            const bNum = parseFloat(bValue.replace(/[£$,]/g, '')) || 0;
            comparison = aNum - bNum;
        } else {
            // String comparison
            if (aValue < bValue) comparison = -1;
            if (aValue > bValue) comparison = 1;
        }
        
        return DashboardState.sortOrder === 'desc' ? -comparison : comparison;
    });
    
    items.forEach(item => container.appendChild(item));
    applyPagination();
}

function updateSortIndicators() {
    const sortButtons = document.querySelectorAll('[data-sort]');
    
    sortButtons.forEach(button => {
        const sortField = button.getAttribute('data-sort');
        const icon = button.querySelector('.sort-icon');
        
        if (icon) {
            icon.className = 'sort-icon fas';
            
            if (sortField === DashboardState.sortField) {
                icon.classList.add(DashboardState.sortOrder === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
                button.classList.add('active');
            } else {
                icon.classList.add('fa-sort');
                button.classList.remove('active');
            }
        }
    });
}

function performSearch(query) {
    const searchableElements = document.querySelectorAll('[data-searchable]');
    
    searchableElements.forEach(element => {
        const searchText = element.textContent.toLowerCase();
        const matches = searchText.includes(query.toLowerCase());
        
        element.style.display = matches || !query ? '' : 'none';
    });
}

function updateFilterCounts() {
    const visibleRows = document.querySelectorAll('[data-filterable]:not([style*="display: none"])');
    const countElement = document.getElementById('filterCount');
    
    if (countElement) {
        countElement.textContent = `${visibleRows.length} items`;
    }
    
    // Update pagination after filtering
    applyPagination();
}

/**
 * Pagination Management
 */
function initializePagination() {
    const paginationContainer = document.getElementById('paginationControls');
    if (!paginationContainer) return;
    
    // Add pagination event listeners
    paginationContainer.addEventListener('click', function(e) {
        if (e.target.matches('[data-page]')) {
            e.preventDefault();
            const page = parseInt(e.target.getAttribute('data-page'));
            goToPage(page);
        }
        
        if (e.target.matches('[data-page-size]')) {
            e.preventDefault();
            const pageSize = parseInt(e.target.getAttribute('data-page-size'));
            changePageSize(pageSize);
        }
    });
    
    applyPagination();
}

function applyPagination() {
    const container = document.querySelector('[data-sortable-container]');
    if (!container) return;
    
    const allItems = Array.from(container.querySelectorAll('[data-sortable]'));
    const visibleItems = allItems.filter(item => item.style.display !== 'none');
    
    const totalItems = visibleItems.length;
    const totalPages = Math.ceil(totalItems / DashboardState.itemsPerPage);
    
    // Ensure current page is valid
    if (DashboardState.currentPage > totalPages) {
        DashboardState.currentPage = Math.max(1, totalPages);
    }
    
    const startIndex = (DashboardState.currentPage - 1) * DashboardState.itemsPerPage;
    const endIndex = startIndex + DashboardState.itemsPerPage;
    
    // Hide all items first
    allItems.forEach(item => {
        if (item.style.display !== 'none') {
            item.classList.add('pagination-hidden');
        }
    });
    
    // Show items for current page
    visibleItems.slice(startIndex, endIndex).forEach(item => {
        item.classList.remove('pagination-hidden');
    });
    
    updatePaginationControls(totalPages, totalItems);
}

function goToPage(page) {
    DashboardState.currentPage = page;
    applyPagination();
}

function changePageSize(pageSize) {
    DashboardState.itemsPerPage = pageSize;
    DashboardState.currentPage = 1; // Reset to first page
    applyPagination();
}

function updatePaginationControls(totalPages, totalItems) {
    const paginationContainer = document.getElementById('paginationControls');
    if (!paginationContainer) return;
    
    const currentPage = DashboardState.currentPage;
    const itemsPerPage = DashboardState.itemsPerPage;
    
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    
    paginationContainer.innerHTML = `
        <div class="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <!-- Results info -->
            <div class="text-sm text-gray-700">
                Showing <span class="font-medium">${startItem}</span> to <span class="font-medium">${endItem}</span> 
                of <span class="font-medium">${totalItems}</span> results
            </div>
            
            <!-- Page size selector -->
            <div class="flex items-center space-x-2">
                <label class="text-sm text-gray-700">Show:</label>
                <select class="border border-gray-300 rounded px-2 py-1 text-sm" onchange="changePageSize(this.value)">
                    <option value="10" ${itemsPerPage === 10 ? 'selected' : ''}>10</option>
                    <option value="25" ${itemsPerPage === 25 ? 'selected' : ''}>25</option>
                    <option value="50" ${itemsPerPage === 50 ? 'selected' : ''}>50</option>
                    <option value="100" ${itemsPerPage === 100 ? 'selected' : ''}>100</option>
                </select>
            </div>
            
            <!-- Pagination buttons -->
            <div class="flex items-center space-x-1">
                ${generatePaginationButtons(currentPage, totalPages)}
            </div>
        </div>
    `;
}

function generatePaginationButtons(currentPage, totalPages) {
    if (totalPages <= 1) return '';
    
    let buttons = [];
    
    // Previous button
    buttons.push(`
        <button class="px-3 py-2 text-sm border border-gray-300 rounded-l-md hover:bg-gray-50 ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : ''}" 
                data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i>
        </button>
    `);
    
    // Page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust start page if we're near the end
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // First page and ellipsis
    if (startPage > 1) {
        buttons.push(`
            <button class="px-3 py-2 text-sm border-t border-b border-gray-300 hover:bg-gray-50" data-page="1">1</button>
        `);
        if (startPage > 2) {
            buttons.push(`<span class="px-3 py-2 text-sm border-t border-b border-gray-300">...</span>`);
        }
    }
    
    // Page number buttons
    for (let i = startPage; i <= endPage; i++) {
        buttons.push(`
            <button class="px-3 py-2 text-sm border-t border-b border-gray-300 hover:bg-gray-50 ${i === currentPage ? 'bg-blue-50 text-blue-600 border-blue-500' : ''}" 
                    data-page="${i}">${i}</button>
        `);
    }
    
    // Last page and ellipsis
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            buttons.push(`<span class="px-3 py-2 text-sm border-t border-b border-gray-300">...</span>`);
        }
        buttons.push(`
            <button class="px-3 py-2 text-sm border-t border-b border-gray-300 hover:bg-gray-50" data-page="${totalPages}">${totalPages}</button>
        `);
    }
    
    // Next button
    buttons.push(`
        <button class="px-3 py-2 text-sm border border-gray-300 rounded-r-md hover:bg-gray-50 ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : ''}" 
                data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="fas fa-chevron-right"></i>
        </button>
    `);
    
    return buttons.join('');
}

/**
 * Form Validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    let isValid = true;
    let errorMessage = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    else if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Phone validation
    else if (fieldType === 'tel' && value) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }
    }
    
    // Custom validation patterns
    const pattern = field.getAttribute('data-pattern');
    if (pattern && value) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            isValid = false;
            errorMessage = field.getAttribute('data-pattern-message') || 'Invalid format';
        }
    }
    
    if (isValid) {
        clearFieldError(field);
    } else {
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error text-red-600 text-sm mt-1';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
}

function clearFieldError(field) {
    field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Mobile Navigation
 */
function initializeMobileNavigation() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    const mobileNavMenu = document.getElementById('mobileNavMenu');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const tabletSidebar = document.getElementById('tabletSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    // Mobile menu handlers
    if (mobileMenuToggle && mobileNavMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileNavMenu.classList.add('active');
            if (mobileNavOverlay) {
                mobileNavOverlay.classList.add('active');
            }
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (mobileMenuClose && mobileNavMenu) {
        mobileMenuClose.addEventListener('click', function() {
            closeMobileMenu();
        });
    }
    
    if (mobileNavOverlay) {
        mobileNavOverlay.addEventListener('click', function() {
            closeMobileMenu();
        });
    }
    
    // Tablet sidebar handlers
    if (sidebarToggle && tabletSidebar) {
        sidebarToggle.addEventListener('click', function() {
            tabletSidebar.classList.add('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.add('active');
            }
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (sidebarClose && tabletSidebar) {
        sidebarClose.addEventListener('click', function() {
            closeTabletSidebar();
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeTabletSidebar();
        });
    }
    
    // Close menus on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
            closeTabletSidebar();
        }
    });
}

function closeMobileMenu() {
    const mobileNavMenu = document.getElementById('mobileNavMenu');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    
    if (mobileNavMenu) {
        mobileNavMenu.classList.remove('active');
    }
    if (mobileNavOverlay) {
        mobileNavOverlay.classList.remove('active');
    }
    document.body.style.overflow = '';
}

function closeTabletSidebar() {
    const tabletSidebar = document.getElementById('tabletSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (tabletSidebar) {
        tabletSidebar.classList.remove('active');
    }
    if (sidebarOverlay) {
        sidebarOverlay.classList.remove('active');
    }
    document.body.style.overflow = '';
}

/**
 * Notification System
 */
function initializeNotifications() {
    const notificationBell = document.querySelector('[data-notifications]');
    
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            toggleNotificationDropdown();
        });
    }
    
    // Close notifications when clicking outside
    document.addEventListener('click', function(e) {
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown && !e.target.closest('[data-notifications]')) {
            notificationDropdown.classList.add('hidden');
        }
    });
    
    // Load initial notifications
    loadNotifications();
}

function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notificationDropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

function loadNotifications() {
    // Simulate loading notifications
    DashboardState.notifications = [
        {
            id: 1,
            type: 'urgent',
            title: 'SLA Warning',
            message: 'Claim CLM-2024-156 approaching deadline',
            timestamp: new Date(Date.now() - 30 * 60 * 1000),
            read: false
        },
        {
            id: 2,
            type: 'info',
            title: 'New Assessment',
            message: 'Assessment request received for Honda Civic',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
            read: false
        },
        {
            id: 3,
            type: 'success',
            title: 'Assessment Complete',
            message: 'CLM-2024-189 assessment completed successfully',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
            read: true
        }
    ];
    
    updateNotificationBadge();
    renderNotifications();
}

function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge');
    const unreadCount = DashboardState.notifications.filter(n => !n.read).length;
    
    if (badge) {
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? 'flex' : 'none';
    }
}

function renderNotifications() {
    const container = document.getElementById('notificationList');
    if (!container) return;
    
    container.innerHTML = '';
    
    DashboardState.notifications.forEach(notification => {
        const notificationElement = createNotificationElement(notification);
        container.appendChild(notificationElement);
    });
}

function createNotificationElement(notification) {
    const div = document.createElement('div');
    div.className = `notification-item p-3 border-b border-gray-200 hover:bg-gray-50 cursor-pointer ${!notification.read ? 'bg-blue-50' : ''}`;
    
    const typeIcon = {
        urgent: 'fas fa-exclamation-triangle text-red-500',
        info: 'fas fa-info-circle text-blue-500',
        success: 'fas fa-check-circle text-green-500'
    }[notification.type] || 'fas fa-bell text-gray-500';
    
    div.innerHTML = `
        <div class="flex items-start space-x-3">
            <i class="${typeIcon}"></i>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">${notification.title}</p>
                <p class="text-sm text-gray-600">${notification.message}</p>
                <p class="text-xs text-gray-500 mt-1">${formatTimestamp(notification.timestamp)}</p>
            </div>
            ${!notification.read ? '<div class="w-2 h-2 bg-blue-500 rounded-full"></div>' : ''}
        </div>
    `;
    
    div.addEventListener('click', function() {
        markNotificationAsRead(notification.id);
    });
    
    return div;
}

function markNotificationAsRead(notificationId) {
    const notification = DashboardState.notifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
        notification.read = true;
        updateNotificationBadge();
        renderNotifications();
    }
}

function formatTimestamp(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
}

/**
 * Interactive Elements
 */
function initializeInteractiveElements() {
    // Action card navigation
    const actionCards = document.querySelectorAll('.action-card[data-url]');
    actionCards.forEach(card => {
        card.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });
    
    // KPI card interactions
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach(card => {
        card.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // Bulk actions
    const bulkActionCheckboxes = document.querySelectorAll('[data-bulk-action]');
    const bulkActionButtons = document.querySelectorAll('[data-bulk-button]');
    
    bulkActionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActionButtons();
        });
    });
    
    bulkActionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-bulk-button');
            const selectedItems = getSelectedBulkItems();
            performBulkAction(action, selectedItems);
        });
    });
    
    // Progress bars animation
    animateProgressBars();
    
    // Tooltip initialization
    initializeTooltips();
}

function updateBulkActionButtons() {
    const selectedCount = getSelectedBulkItems().length;
    const bulkActionContainer = document.getElementById('bulkActions');
    
    if (bulkActionContainer) {
        bulkActionContainer.style.display = selectedCount > 0 ? 'block' : 'none';
    }
    
    const selectedCountElement = document.getElementById('selectedCount');
    if (selectedCountElement) {
        selectedCountElement.textContent = selectedCount;
    }
}

function getSelectedBulkItems() {
    const checkboxes = document.querySelectorAll('[data-bulk-action]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function performBulkAction(action, items) {
    if (items.length === 0) return;
    
    const confirmMessage = `Are you sure you want to ${action} ${items.length} item(s)?`;
    if (confirm(confirmMessage)) {
        // Simulate bulk action
        console.log(`Performing ${action} on items:`, items);
        
        // Show success message
        showNotification(`${action} completed for ${items.length} item(s)`, 'success');
        
        // Clear selections
        document.querySelectorAll('[data-bulk-action]:checked').forEach(cb => {
            cb.checked = false;
        });
        updateBulkActionButtons();
    }
}

function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const targetWidth = bar.style.width || bar.getAttribute('data-width') || '0%';
        bar.style.width = '0%';
        
        setTimeout(() => {
            bar.style.width = targetWidth;
        }, 100);
    });
}

function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element) {
    const tooltipText = element.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    
    tooltip.id = 'tooltip';
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

/**
 * Keyboard Navigation
 */
function initializeKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // Global keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'k':
                    e.preventDefault();
                    focusSearchInput();
                    break;
                case 'n':
                    e.preventDefault();
                    openNewAssessmentModal();
                    break;
            }
        }
        
        // Tab navigation enhancements
        if (e.key === 'Tab') {
            handleTabNavigation(e);
        }
    });
}

function focusSearchInput() {
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

function openNewAssessmentModal() {
    const newAssessmentButton = document.querySelector('[data-modal="newAssessment"]');
    if (newAssessmentButton) {
        newAssessmentButton.click();
    }
}

function handleTabNavigation(e) {
    const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
    }
}

/**
 * Utility Functions
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
    
    const bgColor = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    }[type] || 'bg-blue-500';
    
    notification.classList.add(bgColor, 'text-white');
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

function debounce(func, wait) {
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Export functions for external use
window.DashboardInteractivity = {
    openModal,
    closeModal,
    showNotification,
    toggleSection,
    performSearch,
    validateForm,
    goToPage,
    changePageSize,
    applyPagination,
    initializePagination
};