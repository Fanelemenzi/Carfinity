/**
 * Dashboard Utility Functions and Error Handling
 * Helper functions for formatting, data display, error handling, and loading states
 * Requirements: 8.4, 9.4
 */

class DashboardUtilities {
    constructor() {
        this.loadingStates = new Map();
        this.errorRetryAttempts = new Map();
        this.maxRetryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        
        this.init();
    }
    
    init() {
        this.setupGlobalErrorHandling();
        this.setupNetworkErrorHandling();
        this.setupFormValidation();
        this.setupLoadingStateManagement();
        
        console.log('Dashboard utilities initialized');
    }
    
    /**
     * Data Formatting Helper Functions
     * Requirement 8.4: Helper functions for formatting and data display
     */
    
    // Currency formatting
    formatCurrency(amount, currency = 'USD', locale = 'en-US') {
        try {
            if (amount === null || amount === undefined || isNaN(amount)) {
                return '$0.00';
            }
            
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            }).format(parseFloat(amount));
        } catch (error) {
            console.warn('Currency formatting error:', error);
            return `$${parseFloat(amount || 0).toFixed(2)}`;
        }
    }
    
    // Number formatting with commas
    formatNumber(number, decimals = 0) {
        try {
            if (number === null || number === undefined || isNaN(number)) {
                return '0';
            }
            
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(parseFloat(number));
        } catch (error) {
            console.warn('Number formatting error:', error);
            return parseFloat(number || 0).toFixed(decimals);
        }
    }
    
    // Date formatting
    formatDate(date, options = {}) {
        try {
            if (!date) return 'Not available';
            
            const dateObj = typeof date === 'string' ? new Date(date) : date;
            
            if (isNaN(dateObj.getTime())) {
                return 'Invalid date';
            }
            
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };
            
            const formatOptions = { ...defaultOptions, ...options };
            
            return new Intl.DateTimeFormat('en-US', formatOptions).format(dateObj);
        } catch (error) {
            console.warn('Date formatting error:', error);
            return 'Invalid date';
        }
    }
    
    // Relative time formatting (e.g., "2 days ago")
    formatRelativeTime(date) {
        try {
            if (!date) return 'Unknown';
            
            const dateObj = typeof date === 'string' ? new Date(date) : date;
            const now = new Date();
            const diffInSeconds = Math.floor((now - dateObj) / 1000);
            
            if (diffInSeconds < 60) return 'Just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
            if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
            if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`;
            
            return `${Math.floor(diffInSeconds / 31536000)} years ago`;
        } catch (error) {
            console.warn('Relative time formatting error:', error);
            return 'Unknown';
        }
    }
    
    // Mileage formatting
    formatMileage(mileage, unit = 'mi') {
        try {
            if (mileage === null || mileage === undefined || isNaN(mileage)) {
                return 'Not recorded';
            }
            
            const formatted = this.formatNumber(mileage, 0);
            return `${formatted} ${unit}`;
        } catch (error) {
            console.warn('Mileage formatting error:', error);
            return 'Not recorded';
        }
    }
    
    // Percentage formatting
    formatPercentage(value, decimals = 1) {
        try {
            if (value === null || value === undefined || isNaN(value)) {
                return '0%';
            }
            
            return `${parseFloat(value).toFixed(decimals)}%`;
        } catch (error) {
            console.warn('Percentage formatting error:', error);
            return '0%';
        }
    }
    
    // VIN formatting (truncated display)
    formatVIN(vin, showLength = 8) {
        try {
            if (!vin || typeof vin !== 'string') {
                return 'Not available';
            }
            
            if (vin.length <= showLength) {
                return vin;
            }
            
            return `${vin.slice(0, showLength)}...`;
        } catch (error) {
            console.warn('VIN formatting error:', error);
            return 'Not available';
        }
    }
    
    // Text truncation
    truncateText(text, maxLength = 50, suffix = '...') {
        try {
            if (!text || typeof text !== 'string') {
                return '';
            }
            
            if (text.length <= maxLength) {
                return text;
            }
            
            return text.slice(0, maxLength - suffix.length) + suffix;
        } catch (error) {
            console.warn('Text truncation error:', error);
            return text || '';
        }
    }
    
    // Health status formatting
    formatHealthStatus(score) {
        try {
            const numScore = parseFloat(score);
            
            if (isNaN(numScore)) {
                return { status: 'Unknown', color: 'gray', score: 0 };
            }
            
            if (numScore >= 80) {
                return { status: 'Excellent', color: 'green', score: numScore };
            } else if (numScore >= 60) {
                return { status: 'Good', color: 'blue', score: numScore };
            } else if (numScore >= 40) {
                return { status: 'Fair', color: 'yellow', score: numScore };
            } else {
                return { status: 'Poor', color: 'red', score: numScore };
            }
        } catch (error) {
            console.warn('Health status formatting error:', error);
            return { status: 'Unknown', color: 'gray', score: 0 };
        }
    }
    
    /**
     * Error Handling Functions
     * Requirement 9.4: Error handling for failed operations
     */
    
    setupGlobalErrorHandling() {
        // Global error handler for unhandled JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event.error, event.filename, event.lineno);
        });
        
        // Global handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection(event.reason);
            event.preventDefault(); // Prevent console error
        });
    }
    
    setupNetworkErrorHandling() {
        // Monitor network status
        window.addEventListener('online', () => {
            this.handleNetworkStatusChange(true);
        });
        
        window.addEventListener('offline', () => {
            this.handleNetworkStatusChange(false);
        });
    }
    
    handleGlobalError(error, filename, lineno) {
        console.error('Global error:', error, 'at', filename, ':', lineno);
        
        // Don't show user-facing errors for script loading failures
        if (filename && filename.includes('.js')) {
            return;
        }
        
        this.showErrorNotification('An unexpected error occurred. Please refresh the page.');
    }
    
    handlePromiseRejection(reason) {
        console.error('Unhandled promise rejection:', reason);
        
        // Handle specific error types
        if (reason instanceof TypeError && reason.message.includes('fetch')) {
            this.showErrorNotification('Network error. Please check your connection.');
        } else {
            this.showErrorNotification('An error occurred. Please try again.');
        }
    }
    
    handleNetworkStatusChange(isOnline) {
        if (isOnline) {
            this.showSuccessNotification('Connection restored');
            this.retryFailedRequests();
        } else {
            this.showErrorNotification('Connection lost. Some features may not work.');
        }
    }
    
    // API error handling with retry logic
    async handleApiRequest(requestFn, options = {}) {
        const {
            maxRetries = this.maxRetryAttempts,
            retryDelay = this.retryDelay,
            showErrorToUser = true,
            errorMessage = 'Request failed. Please try again.'
        } = options;
        
        let lastError;
        
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                const result = await requestFn();
                
                // Clear retry count on success
                if (this.errorRetryAttempts.has(requestFn.name)) {
                    this.errorRetryAttempts.delete(requestFn.name);
                }
                
                return result;
            } catch (error) {
                lastError = error;
                console.warn(`API request attempt ${attempt + 1} failed:`, error);
                
                // Don't retry on certain error types
                if (this.isNonRetryableError(error)) {
                    break;
                }
                
                // Wait before retrying (exponential backoff)
                if (attempt < maxRetries) {
                    await this.delay(retryDelay * Math.pow(2, attempt));
                }
            }
        }
        
        // All retries failed
        this.errorRetryAttempts.set(requestFn.name, (this.errorRetryAttempts.get(requestFn.name) || 0) + 1);
        
        if (showErrorToUser) {
            this.showErrorNotification(errorMessage);
        }
        
        throw lastError;
    }
    
    isNonRetryableError(error) {
        // Don't retry on client errors (4xx) except 408, 429
        if (error.status >= 400 && error.status < 500) {
            return ![408, 429].includes(error.status);
        }
        
        // Don't retry on certain error types
        if (error.name === 'AbortError' || error.name === 'TypeError') {
            return true;
        }
        
        return false;
    }
    
    retryFailedRequests() {
        // Implement logic to retry failed requests when connection is restored
        console.log('Retrying failed requests...');
        // This would be implemented based on specific application needs
    }
    
    /**
     * Loading State Management
     * Requirement 8.4: Loading state management and user feedback
     */
    
    setupLoadingStateManagement() {
        // Create global loading overlay template
        this.createLoadingOverlayTemplate();
    }
    
    createLoadingOverlayTemplate() {
        const template = document.createElement('template');
        template.innerHTML = `
            <div class="loading-overlay">
                <div class="loading-spinner-container">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading...</div>
                </div>
            </div>
        `;
        
        this.loadingTemplate = template;
    }
    
    showLoadingState(element, options = {}) {
        const {
            message = 'Loading...',
            overlay = true,
            spinner = true,
            disableElement = true
        } = options;
        
        if (!element) return null;
        
        const loadingId = this.generateLoadingId();
        
        if (overlay) {
            const loadingOverlay = this.createLoadingOverlay(message, spinner);
            loadingOverlay.dataset.loadingId = loadingId;
            
            // Ensure element has relative positioning
            const originalPosition = element.style.position;
            if (!originalPosition || originalPosition === 'static') {
                element.style.position = 'relative';
            }
            
            element.appendChild(loadingOverlay);
            
            // Store original position for cleanup
            this.loadingStates.set(loadingId, {
                element,
                overlay: loadingOverlay,
                originalPosition,
                originalDisabled: element.disabled
            });
        }
        
        if (disableElement && element.tagName === 'BUTTON') {
            element.disabled = true;
        }
        
        // Add loading class for CSS styling
        element.classList.add('loading-state');
        
        return loadingId;
    }
    
    hideLoadingState(loadingId) {
        const loadingState = this.loadingStates.get(loadingId);
        
        if (!loadingState) return;
        
        const { element, overlay, originalPosition, originalDisabled } = loadingState;
        
        // Remove overlay with animation
        if (overlay) {
            overlay.classList.add('fade-out');
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                
                // Restore original position
                if (!originalPosition || originalPosition === 'static') {
                    element.style.position = originalPosition || '';
                }
            }, 300);
        }
        
        // Restore element state
        if (element.tagName === 'BUTTON') {
            element.disabled = originalDisabled || false;
        }
        
        element.classList.remove('loading-state');
        
        // Clean up
        this.loadingStates.delete(loadingId);
    }
    
    createLoadingOverlay(message, showSpinner) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay active';
        
        let content = '';
        if (showSpinner) {
            content += '<div class="loading-spinner"></div>';
        }
        if (message) {
            content += `<div class="loading-text">${message}</div>`;
        }
        
        overlay.innerHTML = `
            <div class="loading-content">
                ${content}
            </div>
        `;
        
        return overlay;
    }
    
    generateLoadingId() {
        return 'loading_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Skeleton loading for content placeholders
    showSkeletonLoading(container, options = {}) {
        const {
            lines = 3,
            height = '1rem',
            spacing = '0.5rem',
            animation = true
        } = options;
        
        if (!container) return;
        
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-container';
        
        for (let i = 0; i < lines; i++) {
            const line = document.createElement('div');
            line.className = `skeleton-line ${animation ? 'skeleton-animate' : ''}`;
            line.style.height = height;
            line.style.marginBottom = i < lines - 1 ? spacing : '0';
            
            // Vary width for more realistic appearance
            if (i === lines - 1) {
                line.style.width = '60%';
            }
            
            skeleton.appendChild(line);
        }
        
        container.innerHTML = '';
        container.appendChild(skeleton);
        
        return skeleton;
    }
    
    hideSkeletonLoading(container) {
        if (!container) return;
        
        const skeleton = container.querySelector('.skeleton-container');
        if (skeleton) {
            skeleton.remove();
        }
    }
    
    /**
     * Form Validation and Error Display
     */
    
    setupFormValidation() {
        // Enhanced form validation with custom error messages
        document.addEventListener('invalid', (e) => {
            e.preventDefault();
            this.showFieldError(e.target);
        }, true);
        
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.clearFieldError(e.target);
            }
        });
    }
    
    showFieldError(field, message = null) {
        this.clearFieldError(field);
        
        const errorMessage = message || this.getValidationMessage(field);
        const errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        errorElement.textContent = errorMessage;
        errorElement.setAttribute('role', 'alert');
        
        // Add error styling to field
        field.classList.add('error');
        field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', `error-${field.name || field.id}`);
        errorElement.id = `error-${field.name || field.id}`;
        
        // Insert error message after field
        field.parentNode.insertBefore(errorElement, field.nextSibling);
        
        // Animate error appearance
        requestAnimationFrame(() => {
            errorElement.classList.add('show');
        });
    }
    
    clearFieldError(field) {
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
        
        field.classList.remove('error');
        field.removeAttribute('aria-invalid');
        field.removeAttribute('aria-describedby');
    }
    
    getValidationMessage(field) {
        if (field.validity.valueMissing) {
            return `${this.getFieldLabel(field)} is required.`;
        }
        if (field.validity.typeMismatch) {
            return `Please enter a valid ${field.type}.`;
        }
        if (field.validity.tooShort) {
            return `${this.getFieldLabel(field)} must be at least ${field.minLength} characters.`;
        }
        if (field.validity.tooLong) {
            return `${this.getFieldLabel(field)} must be no more than ${field.maxLength} characters.`;
        }
        if (field.validity.rangeUnderflow) {
            return `${this.getFieldLabel(field)} must be at least ${field.min}.`;
        }
        if (field.validity.rangeOverflow) {
            return `${this.getFieldLabel(field)} must be no more than ${field.max}.`;
        }
        if (field.validity.patternMismatch) {
            return `${this.getFieldLabel(field)} format is invalid.`;
        }
        
        return 'Please correct this field.';
    }
    
    getFieldLabel(field) {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label) {
            return label.textContent.replace('*', '').trim();
        }
        
        return field.placeholder || field.name || 'This field';
    }
    
    /**
     * Notification System
     */
    
    showSuccessNotification(message, duration = 3000) {
        this.showNotification(message, 'success', duration);
    }
    
    showErrorNotification(message, duration = 5000) {
        this.showNotification(message, 'error', duration);
    }
    
    showInfoNotification(message, duration = 3000) {
        this.showNotification(message, 'info', duration);
    }
    
    showWarningNotification(message, duration = 4000) {
        this.showNotification(message, 'warning', duration);
    }
    
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getNotificationIcon(type);
        
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${icon} notification-icon"></i>
                <span class="notification-message">${message}</span>
                <button class="notification-close" aria-label="Close notification">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add to notification container or create one
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Setup close button
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }
        
        return notification;
    }
    
    hideNotification(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        return icons[type] || icons.info;
    }
    
    /**
     * Utility Helper Functions
     */
    
    // Debounce function
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
    
    // Throttle function
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Delay function
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Deep clone object
    deepClone(obj) {
        try {
            return JSON.parse(JSON.stringify(obj));
        } catch (error) {
            console.warn('Deep clone error:', error);
            return obj;
        }
    }
    
    // Check if element is in viewport
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Smooth scroll to element
    scrollToElement(element, options = {}) {
        const defaultOptions = {
            behavior: 'smooth',
            block: 'start',
            inline: 'nearest'
        };
        
        const scrollOptions = { ...defaultOptions, ...options };
        
        if (element && typeof element.scrollIntoView === 'function') {
            element.scrollIntoView(scrollOptions);
        }
    }
    
    // Local storage with error handling
    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Local storage set error:', error);
            return false;
        }
    }
    
    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Local storage get error:', error);
            return defaultValue;
        }
    }
    
    removeLocalStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Local storage remove error:', error);
            return false;
        }
    }
    
    // Cleanup method
    cleanup() {
        // Clear all loading states
        this.loadingStates.forEach((state, id) => {
            this.hideLoadingState(id);
        });
        
        // Clear retry attempts
        this.errorRetryAttempts.clear();
    }
}

// CSS for utilities and error handling
const utilitiesCSS = `
/* Loading overlay styles */
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.loading-overlay.active {
    opacity: 1;
}

.loading-overlay.fade-out {
    opacity: 0;
}

.loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.loading-spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid #e5e7eb;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.loading-text {
    color: #6b7280;
    font-size: 0.875rem;
    font-weight: 500;
}

/* Skeleton loading styles */
.skeleton-container {
    padding: 1rem 0;
}

.skeleton-line {
    background: #e5e7eb;
    border-radius: 0.25rem;
    width: 100%;
}

.skeleton-animate {
    background: linear-gradient(90deg, #e5e7eb 25%, #d1d5db 50%, #e5e7eb 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* Form error styles */
.field-error {
    color: #dc2626;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    opacity: 0;
    transform: translateY(-0.5rem);
    transition: all 0.3s ease;
}

.field-error.show {
    opacity: 1;
    transform: translateY(0);
}

input.error,
textarea.error,
select.error {
    border-color: #dc2626;
    box-shadow: 0 0 0 1px #dc2626;
}

/* Notification styles */
.notification-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 24rem;
}

.notification {
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    transform: translateX(100%);
    transition: transform 0.3s ease;
}

.notification.show {
    transform: translateX(0);
}

.notification.hide {
    transform: translateX(100%);
}

.notification-success {
    background: #10b981;
    color: white;
}

.notification-error {
    background: #dc2626;
    color: white;
}

.notification-warning {
    background: #f59e0b;
    color: white;
}

.notification-info {
    background: #3b82f6;
    color: white;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.notification-message {
    flex: 1;
    font-size: 0.875rem;
    font-weight: 500;
}

.notification-close {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    opacity: 0.8;
    transition: opacity 0.2s ease;
}

.notification-close:hover {
    opacity: 1;
}

/* Loading state for elements */
.loading-state {
    pointer-events: none;
    opacity: 0.7;
}

/* Spin animation */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Responsive adjustments */
@media (max-width: 640px) {
    .notification-container {
        left: 1rem;
        right: 1rem;
        max-width: none;
    }
    
    .notification {
        padding: 0.75rem;
    }
    
    .notification-message {
        font-size: 0.8125rem;
    }
}
`;

// Inject CSS
const utilitiesStyleSheet = document.createElement('style');
utilitiesStyleSheet.textContent = utilitiesCSS;
document.head.appendChild(utilitiesStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardUtilities = new DashboardUtilities();
});

// Export for external use
window.DashboardUtilities = DashboardUtilities;