/**
 * Essential UI Components JavaScript
 * Handles basic search, filter functionality, loading states, and form validation
 * Focuses on essential interactions without complex notification systems
 */

// Global state for UI components
const UIComponentsState = {
    activeSearches: new Map(),
    loadingStates: new Map(),
    validationErrors: new Map(),
    formStates: new Map()
};

// Initialize essential UI components when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeEssentialUIComponents();
});

/**
 * Main initialization function for essential UI components
 */
function initializeEssentialUIComponents() {
    setupBasicSearchAndFilter();
    setupLoadingStates();
    setupFormValidation();
    setupUserFeedback();
    setupEssentialInteractions();
    setupAccessibilityFeatures();
}

/**
 * Setup basic search and filter functionality
 */
function setupBasicSearchAndFilter() {
    // Enhanced global search functionality
    const searchInputs = document.querySelectorAll('[data-search], #globalSearch');

    searchInputs.forEach(input => {
        setupSearchInput(input);
    });

    // Setup filter dropdowns
    const filterSelects = document.querySelectorAll('[data-filter]');
    filterSelects.forEach(select => {
        setupFilterSelect(select);
    });

    // Setup date range filters
    const dateInputs = document.querySelectorAll('input[type="date"][data-filter]');
    dateInputs.forEach(input => {
        setupDateFilter(input);
    });

    // Setup clear filters functionality
    const clearButtons = document.querySelectorAll('[data-clear-filters]');
    clearButtons.forEach(button => {
        button.addEventListener('click', clearAllFilters);
    });
}

/**
 * Setup individual search input
 */
function setupSearchInput(input) {
    let searchTimeout;
    const searchDelay = 300; // ms

    // Add search icon if not present
    addSearchIcon(input);

    // Setup input event with debouncing
    input.addEventListener('input', function () {
        const query = this.value.trim();
        const searchId = this.id || 'default';

        clearTimeout(searchTimeout);

        // Show loading state
        showSearchLoading(this);

        searchTimeout = setTimeout(() => {
            performSearch(query, searchId, this);
            hideSearchLoading(this);
        }, searchDelay);

        // Store active search
        UIComponentsState.activeSearches.set(searchId, query);
    });

    // Clear search on escape
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            this.value = '';
            const searchId = this.id || 'default';
            performSearch('', searchId, this);
            UIComponentsState.activeSearches.delete(searchId);
            this.blur();
        }
    });

    // Focus handling
    input.addEventListener('focus', function () {
        this.parentElement.classList.add('search-focused');
    });

    input.addEventListener('blur', function () {
        this.parentElement.classList.remove('search-focused');
    });
}

/**
 * Add search icon to input if not present
 */
function addSearchIcon(input) {
    const parent = input.parentElement;
    if (!parent.querySelector('.search-icon')) {
        const icon = document.createElement('i');
        icon.className = 'search-icon fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none';

        // Make parent relative if not already
        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        parent.insertBefore(icon, input);

        // Add padding to input to account for icon
        if (!input.style.paddingLeft) {
            input.style.paddingLeft = '2.5rem';
        }
    }
}

/**
 * Show search loading state
 */
function showSearchLoading(input) {
    const icon = input.parentElement.querySelector('.search-icon');
    if (icon) {
        icon.className = 'search-icon fas fa-spinner fa-spin absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none';
    }
}

/**
 * Hide search loading state
 */
function hideSearchLoading(input) {
    const icon = input.parentElement.querySelector('.search-icon');
    if (icon) {
        icon.className = 'search-icon fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none';
    }
}

/**
 * Perform search operation
 */
function performSearch(query, searchId, inputElement) {
    const searchableElements = document.querySelectorAll('[data-searchable]');
    let matchCount = 0;

    searchableElements.forEach(element => {
        const searchText = element.textContent.toLowerCase();
        const matches = !query || searchText.includes(query.toLowerCase());

        // Show/hide element based on search match
        if (matches) {
            element.style.display = '';
            matchCount++;
        } else {
            element.style.display = 'none';
        }

        // Add search highlight if query exists and matches
        if (query && matches) {
            highlightSearchTerms(element, query);
        } else {
            removeSearchHighlights(element);
        }
    });

    // Update search results count
    updateSearchResultsCount(matchCount, query, inputElement);

    // Trigger custom search event
    const searchEvent = new CustomEvent('searchPerformed', {
        detail: { query, matchCount, searchId }
    });
    document.dispatchEvent(searchEvent);
}

/**
 * Highlight search terms in element
 */
function highlightSearchTerms(element, query) {
    // Remove existing highlights first
    removeSearchHighlights(element);

    if (!query) return;

    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    const textNodes = [];
    let node;

    while (node = walker.nextNode()) {
        textNodes.push(node);
    }

    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');

        if (regex.test(text)) {
            const highlightedHTML = text.replace(regex, '<mark class="search-highlight bg-yellow-200">$1</mark>');
            const wrapper = document.createElement('span');
            wrapper.innerHTML = highlightedHTML;
            textNode.parentNode.replaceChild(wrapper, textNode);
        }
    });
}

/**
 * Remove search highlights from element
 */
function removeSearchHighlights(element) {
    const highlights = element.querySelectorAll('.search-highlight');
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
        parent.normalize();
    });
}

/**
 * Escape special regex characters
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Update search results count display
 */
function updateSearchResultsCount(count, query, inputElement) {
    const countElement = document.getElementById('searchResultsCount') ||
        inputElement.parentElement.querySelector('.search-results-count');

    if (countElement) {
        if (query) {
            countElement.textContent = `${count} result${count !== 1 ? 's' : ''} found`;
            countElement.style.display = 'block';
        } else {
            countElement.style.display = 'none';
        }
    }
}

/**
 * Setup filter select elements
 */
function setupFilterSelect(select) {
    select.addEventListener('change', function () {
        const filterType = this.getAttribute('data-filter');
        const filterValue = this.value;

        // Show loading state
        showFilterLoading(this);

        // Apply filter with slight delay for UX
        setTimeout(() => {
            applyFilter(filterType, filterValue);
            hideFilterLoading(this);
        }, 100);
    });

    // Add custom styling for better UX
    enhanceSelectStyling(select);
}

/**
 * Setup date filter inputs
 */
function setupDateFilter(input) {
    input.addEventListener('change', function () {
        const filterType = this.getAttribute('data-filter');
        const filterValue = this.value;

        applyFilter(filterType, filterValue);
    });

    // Add date picker enhancements
    enhanceDateInput(input);
}

/**
 * Apply individual filter
 */
function applyFilter(filterType, filterValue) {
    const filterableElements = document.querySelectorAll('[data-filterable]');
    let visibleCount = 0;

    filterableElements.forEach(element => {
        const elementValue = element.getAttribute(`data-${filterType}`);
        let shouldShow = true;

        if (filterValue && filterValue !== '') {
            if (filterType === 'date') {
                // Date filtering logic
                const elementDate = new Date(elementValue);
                const filterDate = new Date(filterValue);
                shouldShow = elementDate >= filterDate;
            } else {
                shouldShow = elementValue === filterValue;
            }
        }

        if (shouldShow) {
            element.style.display = '';
            visibleCount++;
        } else {
            element.style.display = 'none';
        }
    });

    // Update filter count
    updateFilterCount(visibleCount);

    // Trigger custom filter event
    const filterEvent = new CustomEvent('filterApplied', {
        detail: { filterType, filterValue, visibleCount }
    });
    document.dispatchEvent(filterEvent);
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    // Clear all filter inputs
    const filterInputs = document.querySelectorAll('[data-filter]');
    filterInputs.forEach(input => {
        input.value = '';
    });

    // Clear search inputs
    const searchInputs = document.querySelectorAll('[data-search], #globalSearch');
    searchInputs.forEach(input => {
        input.value = '';
        removeSearchHighlights(document.body);
    });

    // Show all filterable elements
    const filterableElements = document.querySelectorAll('[data-filterable]');
    filterableElements.forEach(element => {
        element.style.display = '';
    });

    // Clear search highlights
    removeSearchHighlights(document.body);

    // Update counts
    updateFilterCount(filterableElements.length);
    updateSearchResultsCount(0, '', null);

    // Clear state
    UIComponentsState.activeSearches.clear();

    // Show success feedback
    showUserFeedback('All filters cleared', 'success');
}

/**
 * Update filter count display
 */
function updateFilterCount(count) {
    const countElements = document.querySelectorAll('[data-filter-count]');
    countElements.forEach(element => {
        element.textContent = `${count} item${count !== 1 ? 's' : ''} shown`;
    });
}

/**
 * Show filter loading state
 */
function showFilterLoading(select) {
    const parent = select.parentElement;
    if (!parent.querySelector('.filter-loading')) {
        const loader = document.createElement('div');
        loader.className = 'filter-loading absolute right-8 top-1/2 transform -translate-y-1/2';
        loader.innerHTML = '<i class="fas fa-spinner fa-spin text-gray-400 text-sm"></i>';

        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        parent.appendChild(loader);
    }
}

/**
 * Hide filter loading state
 */
function hideFilterLoading(select) {
    const loader = select.parentElement.querySelector('.filter-loading');
    if (loader) {
        loader.remove();
    }
}

/**
 * Setup loading states for data operations
 */
function setupLoadingStates() {
    // Create global loading functions
    window.showLoading = function (elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (!element) return;

        UIComponentsState.loadingStates.set(elementId, true);

        // Create loading overlay
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-20';
        loadingOverlay.innerHTML = `
            <div class="flex flex-col items-center space-y-2">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <span class="text-sm text-gray-600">${message}</span>
            </div>
        `;

        // Make parent relative if needed
        if (getComputedStyle(element).position === 'static') {
            element.style.position = 'relative';
        }

        element.appendChild(loadingOverlay);
    };

    window.hideLoading = function (elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        UIComponentsState.loadingStates.delete(elementId);

        const loadingOverlay = element.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    };

    // Setup button loading states
    setupButtonLoadingStates();
}

/**
 * Setup button loading states
 */
function setupButtonLoadingStates() {
    document.addEventListener('click', function (e) {
        const button = e.target.closest('[data-loading]');
        if (button) {
            showButtonLoading(button);

            // Auto-hide after timeout if not manually hidden
            const timeout = parseInt(button.getAttribute('data-loading-timeout')) || 3000;
            setTimeout(() => {
                hideButtonLoading(button);
            }, timeout);
        }
    });
}

/**
 * Show button loading state
 */
function showButtonLoading(button) {
    if (button.classList.contains('loading')) return;

    button.classList.add('loading');
    button.disabled = true;

    // Store original content
    button.setAttribute('data-original-content', button.innerHTML);

    // Show loading content
    const loadingText = button.getAttribute('data-loading-text') || 'Loading...';
    button.innerHTML = `
        <i class="fas fa-spinner fa-spin mr-2"></i>
        ${loadingText}
    `;
}

/**
 * Hide button loading state
 */
function hideButtonLoading(button) {
    if (!button.classList.contains('loading')) return;

    button.classList.remove('loading');
    button.disabled = false;

    // Restore original content
    const originalContent = button.getAttribute('data-original-content');
    if (originalContent) {
        button.innerHTML = originalContent;
        button.removeAttribute('data-original-content');
    }
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
        setupFormValidationHandlers(form);
    });

    // Setup real-time validation for inputs
    document.addEventListener('blur', function (e) {
        if (e.target.matches('input, select, textarea')) {
            validateField(e.target);
        }
    }, true);

    document.addEventListener('input', function (e) {
        if (e.target.matches('input, select, textarea')) {
            clearFieldError(e.target);
        }
    });
}

/**
 * Setup form validation handlers
 */
function setupFormValidationHandlers(form) {
    form.addEventListener('submit', function (e) {
        if (!validateForm(this)) {
            e.preventDefault();
            showUserFeedback('Please correct the errors below', 'error');

            // Focus first invalid field
            const firstInvalid = this.querySelector('.field-error');
            if (firstInvalid) {
                const field = firstInvalid.previousElementSibling;
                if (field) {
                    field.focus();
                }
            }
        }
    });

    // Store form state
    const formId = form.id || 'form_' + Date.now();
    UIComponentsState.formStates.set(formId, {
        isValid: false,
        errors: new Map()
    });
}

/**
 * Validate entire form
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    const formId = form.id || 'form_' + Date.now();
    const formState = UIComponentsState.formStates.get(formId) || { errors: new Map() };

    // Clear previous errors
    formState.errors.clear();

    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    // Validate custom validation rules
    const customValidationFields = form.querySelectorAll('[data-validation]');
    customValidationFields.forEach(field => {
        if (!validateCustomRules(field)) {
            isValid = false;
        }
    });

    formState.isValid = isValid;
    UIComponentsState.formStates.set(formId, formState);

    return isValid;
}

/**
 * Validate individual field
 */
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
    // URL validation
    else if (fieldType === 'url' && value) {
        try {
            new URL(value);
        } catch {
            isValid = false;
            errorMessage = 'Please enter a valid URL';
        }
    }
    // Number validation
    else if (fieldType === 'number' && value) {
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        const numValue = parseFloat(value);

        if (isNaN(numValue)) {
            isValid = false;
            errorMessage = 'Please enter a valid number';
        } else if (min && numValue < parseFloat(min)) {
            isValid = false;
            errorMessage = `Value must be at least ${min}`;
        } else if (max && numValue > parseFloat(max)) {
            isValid = false;
            errorMessage = `Value must be no more than ${max}`;
        }
    }
    // Pattern validation
    const pattern = field.getAttribute('pattern');
    if (pattern && value) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            isValid = false;
            errorMessage = field.getAttribute('title') || 'Invalid format';
        }
    }

    // Min/max length validation
    const minLength = field.getAttribute('minlength');
    const maxLength = field.getAttribute('maxlength');

    if (minLength && value.length < parseInt(minLength)) {
        isValid = false;
        errorMessage = `Must be at least ${minLength} characters`;
    } else if (maxLength && value.length > parseInt(maxLength)) {
        isValid = false;
        errorMessage = `Must be no more than ${maxLength} characters`;
    }

    if (isValid) {
        clearFieldError(field);
    } else {
        showFieldError(field, errorMessage);
    }

    return isValid;
}

/**
 * Validate custom validation rules
 */
function validateCustomRules(field) {
    const validationRules = field.getAttribute('data-validation');
    if (!validationRules) return true;

    const rules = validationRules.split('|');
    let isValid = true;

    rules.forEach(rule => {
        const [ruleName, ruleValue] = rule.split(':');

        switch (ruleName) {
            case 'match':
                const matchField = document.getElementById(ruleValue);
                if (matchField && field.value !== matchField.value) {
                    isValid = false;
                    showFieldError(field, 'Fields do not match');
                }
                break;
            case 'unique':
                // Custom unique validation would go here
                break;
        }
    });

    return isValid;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    clearFieldError(field);

    field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    field.setAttribute('aria-invalid', 'true');

    const errorElement = document.createElement('div');
    errorElement.className = 'field-error text-red-600 text-sm mt-1';
    errorElement.textContent = message;
    errorElement.setAttribute('role', 'alert');

    field.parentNode.appendChild(errorElement);

    // Store error in state
    const fieldId = field.id || field.name || 'unknown';
    UIComponentsState.validationErrors.set(fieldId, message);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    field.removeAttribute('aria-invalid');

    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }

    // Remove error from state
    const fieldId = field.id || field.name || 'unknown';
    UIComponentsState.validationErrors.delete(fieldId);
}

/**
 * Setup user feedback system (simple, non-complex notifications)
 */
function setupUserFeedback() {
    // Create feedback container if it doesn't exist
    if (!document.getElementById('feedbackContainer')) {
        const container = document.createElement('div');
        container.id = 'feedbackContainer';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }
}

/**
 * Show user feedback message
 */
function showUserFeedback(message, type = 'info', duration = 4000) {
    const container = document.getElementById('feedbackContainer');
    if (!container) return;

    const feedback = document.createElement('div');
    feedback.className = `feedback-message p-3 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full max-w-sm`;

    // Set type-specific styling
    const typeClasses = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };

    const typeIcons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    feedback.classList.add(...typeClasses[type].split(' '));

    feedback.innerHTML = `
        <div class="flex items-center">
            <i class="${typeIcons[type]} mr-2"></i>
            <span class="flex-1">${message}</span>
            <button class="ml-2 text-white hover:text-gray-200 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(feedback);

    // Animate in
    setTimeout(() => {
        feedback.classList.remove('translate-x-full');
    }, 100);

    // Auto remove after duration
    setTimeout(() => {
        feedback.classList.add('translate-x-full');
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.remove();
            }
        }, 300);
    }, duration);
}

/**
 * Setup essential interactions
 */
function setupEssentialInteractions() {
    // Setup dropdown toggles
    setupDropdownToggles();

    // Setup collapsible sections
    setupCollapsibleSections();

    // Setup copy to clipboard functionality
    setupCopyToClipboard();

    // Setup confirmation dialogs
    setupConfirmationDialogs();

    // Setup auto-save functionality
    setupAutoSave();
}

/**
 * Setup dropdown toggles
 */
function setupDropdownToggles() {
    document.addEventListener('click', function (e) {
        const toggle = e.target.closest('[data-dropdown-toggle]');

        if (toggle) {
            e.preventDefault();
            const targetId = toggle.getAttribute('data-dropdown-toggle');
            const dropdown = document.getElementById(targetId);

            if (dropdown) {
                const isOpen = !dropdown.classList.contains('hidden');

                // Close all other dropdowns
                document.querySelectorAll('[data-dropdown]').forEach(dd => {
                    dd.classList.add('hidden');
                });

                // Toggle current dropdown
                if (isOpen) {
                    dropdown.classList.add('hidden');
                } else {
                    dropdown.classList.remove('hidden');
                }
            }
        } else {
            // Close dropdowns when clicking outside
            const dropdown = e.target.closest('[data-dropdown]');
            if (!dropdown) {
                document.querySelectorAll('[data-dropdown]').forEach(dd => {
                    dd.classList.add('hidden');
                });
            }
        }
    });
}

/**
 * Setup collapsible sections
 */
function setupCollapsibleSections() {
    document.addEventListener('click', function (e) {
        const toggle = e.target.closest('[data-collapse-toggle]');

        if (toggle) {
            const targetId = toggle.getAttribute('data-collapse-toggle');
            const target = document.getElementById(targetId);

            if (target) {
                const isCollapsed = target.classList.contains('collapsed');

                if (isCollapsed) {
                    target.classList.remove('collapsed');
                    target.style.maxHeight = target.scrollHeight + 'px';
                    toggle.setAttribute('aria-expanded', 'true');
                } else {
                    target.classList.add('collapsed');
                    target.style.maxHeight = '0';
                    toggle.setAttribute('aria-expanded', 'false');
                }

                // Update toggle icon
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down', isCollapsed);
                    icon.classList.toggle('fa-chevron-up', !isCollapsed);
                }
            }
        }
    });
}

/**
 * Setup copy to clipboard functionality
 */
function setupCopyToClipboard() {
    document.addEventListener('click', function (e) {
        const copyButton = e.target.closest('[data-copy]');

        if (copyButton) {
            const textToCopy = copyButton.getAttribute('data-copy');
            const targetElement = document.getElementById(textToCopy);
            const text = targetElement ? targetElement.textContent : textToCopy;

            navigator.clipboard.writeText(text).then(() => {
                showUserFeedback('Copied to clipboard', 'success', 2000);

                // Visual feedback on button
                const originalText = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check mr-1"></i>Copied!';
                copyButton.classList.add('bg-green-500', 'text-white');

                setTimeout(() => {
                    copyButton.innerHTML = originalText;
                    copyButton.classList.remove('bg-green-500', 'text-white');
                }, 1000);
            }).catch(() => {
                showUserFeedback('Failed to copy to clipboard', 'error');
            });
        }
    });
}

/**
 * Setup confirmation dialogs
 */
function setupConfirmationDialogs() {
    document.addEventListener('click', function (e) {
        const confirmButton = e.target.closest('[data-confirm]');

        if (confirmButton) {
            const message = confirmButton.getAttribute('data-confirm');
            const confirmed = confirm(message);

            if (!confirmed) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        }
    });
}

/**
 * Setup auto-save functionality
 */
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');

    autoSaveForms.forEach(form => {
        const saveInterval = parseInt(form.getAttribute('data-auto-save')) || 30000; // 30 seconds default
        let saveTimeout;

        form.addEventListener('input', function () {
            clearTimeout(saveTimeout);

            saveTimeout = setTimeout(() => {
                autoSaveForm(form);
            }, saveInterval);
        });
    });
}

/**
 * Auto-save form data
 */
function autoSaveForm(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const formId = form.id || 'form_' + Date.now();

    // Save to localStorage
    localStorage.setItem(`autosave_${formId}`, JSON.stringify({
        data: data,
        timestamp: Date.now()
    }));

    showUserFeedback('Draft saved', 'info', 2000);
}

/**
 * Setup accessibility features
 */
function setupAccessibilityFeatures() {
    // Skip links
    setupSkipLinks();

    // Focus management
    setupFocusManagement();

    // Keyboard navigation
    setupKeyboardNavigation();

    // Screen reader announcements
    setupScreenReaderAnnouncements();
}

/**
 * Setup skip links
 */
function setupSkipLinks() {
    const skipLinks = document.querySelectorAll('.skip-link');

    skipLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);

            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * Setup focus management
 */
function setupFocusManagement() {
    // Focus trap for modals
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
            const modal = document.querySelector('.modal:not(.hidden)');
            if (modal) {
                trapFocus(e, modal);
            }
        }
    });
}

/**
 * Trap focus within element
 */
function trapFocus(e, container) {
    const focusableElements = container.querySelectorAll(
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
 * Setup keyboard navigation
 */
function setupKeyboardNavigation() {
    // Arrow key navigation for lists
    document.addEventListener('keydown', function (e) {
        const list = e.target.closest('[role="listbox"], [role="menu"]');
        if (list) {
            handleListNavigation(e, list);
        }
    });
}

/**
 * Handle list navigation with arrow keys
 */
function handleListNavigation(e, list) {
    const items = Array.from(list.querySelectorAll('[role="option"], [role="menuitem"]'));
    const currentIndex = items.indexOf(document.activeElement);

    let nextIndex = currentIndex;

    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            nextIndex = (currentIndex + 1) % items.length;
            break;
        case 'ArrowUp':
            e.preventDefault();
            nextIndex = (currentIndex - 1 + items.length) % items.length;
            break;
        case 'Home':
            e.preventDefault();
            nextIndex = 0;
            break;
        case 'End':
            e.preventDefault();
            nextIndex = items.length - 1;
            break;
    }

    if (nextIndex !== currentIndex && items[nextIndex]) {
        items[nextIndex].focus();
    }
}

/**
 * Setup screen reader announcements
 */
function setupScreenReaderAnnouncements() {
    // Create live region for announcements
    if (!document.getElementById('sr-announcements')) {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'sr-announcements';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        document.body.appendChild(liveRegion);
    }
}

/**
 * Announce to screen readers
 */
function announceToScreenReader(message) {
    const liveRegion = document.getElementById('sr-announcements');
    if (liveRegion) {
        liveRegion.textContent = message;

        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
}

/**
 * Enhance select styling
 */
function enhanceSelectStyling(select) {
    // Add custom arrow if not present
    const parent = select.parentElement;
    if (!parent.querySelector('.select-arrow')) {
        const arrow = document.createElement('div');
        arrow.className = 'select-arrow absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none';
        arrow.innerHTML = '<i class="fas fa-chevron-down text-gray-400"></i>';

        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        parent.appendChild(arrow);
    }
}

/**
 * Enhance date input
 */
function enhanceDateInput(input) {
    // Add calendar icon
    const parent = input.parentElement;
    if (!parent.querySelector('.date-icon')) {
        const icon = document.createElement('div');
        icon.className = 'date-icon absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none';
        icon.innerHTML = '<i class="fas fa-calendar text-gray-400"></i>';

        if (getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }

        parent.appendChild(icon);
    }
}

// Export functions for global access
window.EssentialUIComponents = {
    showUserFeedback,
    showLoading,
    hideLoading,
    showButtonLoading,
    hideButtonLoading,
    validateForm,
    validateField,
    clearAllFilters,
    announceToScreenReader,
    autoSaveForm
};

// Make key functions globally available
window.showUserFeedback = showUserFeedback;
window.showLoading = showLoading;
window.hideLoading = hideLoading;