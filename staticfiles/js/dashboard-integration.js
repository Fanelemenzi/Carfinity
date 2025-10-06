/**
 * Dashboard Integration Script
 * Final integration layer that coordinates all dashboard components
 */

class DashboardIntegration {
    constructor() {
        this.components = new Map();
        this.initialized = false;
        this.performanceMetrics = {};
        this.initializationAttempts = 0;
        this.maxInitializationAttempts = 3;
        
        // Check if we're in a reload loop
        const reloadCount = parseInt(sessionStorage.getItem('dashboardReloadCount') || '0');
        if (reloadCount > 2) {
            console.warn('Multiple dashboard reload attempts detected, using safe mode');
            this.safeMode = true;
            sessionStorage.removeItem('dashboardReloadCount');
        } else {
            this.safeMode = false;
        }
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready and give other scripts time to initialize
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                // Add a small delay to ensure other scripts have initialized
                setTimeout(() => this.initialize(), 100);
            });
        } else {
            // Add a small delay to ensure other scripts have initialized
            setTimeout(() => this.initialize(), 100);
        }
    }
    
    async initialize() {
        this.initializationAttempts++;
        console.log(`🚀 Initializing Dashboard Integration (attempt ${this.initializationAttempts})...`);
        
        try {
            // Start performance monitoring
            this.startPerformanceMonitoring();
            
            // Initialize core components (non-blocking)
            await this.initializeComponents();
            
            // Setup cross-component communication
            this.setupComponentCommunication();
            
            // Setup global event handlers
            this.setupGlobalEventHandlers();
            
            // Setup accessibility features
            this.setupAccessibility();
            
            // Setup error handling
            this.setupErrorHandling();
            
            // Final optimizations (non-blocking)
            this.finalOptimizations();
            
            this.initialized = true;
            console.log('✅ Dashboard Integration initialized successfully');
            
            // Clear any reload count on successful initialization
            sessionStorage.removeItem('dashboardReloadCount');
            
            // Dispatch ready event
            this.dispatchReadyEvent();
            
        } catch (error) {
            console.error('❌ Dashboard Integration initialization failed:', error);
            
            // Only show fallback UI for critical errors
            if (this.isCriticalError(error)) {
                this.handleInitializationError(error);
            } else {
                // For non-critical errors, continue with partial initialization
                console.warn('⚠️ Dashboard Integration initialized with warnings');
                this.initialized = true;
                this.dispatchReadyEvent();
            }
        }
    }
    
    async initializeComponents() {
        const componentPromises = [];
        
        // Initialize navigation
        componentPromises.push(this.initializeNavigation());
        
        // Initialize notifications
        componentPromises.push(this.initializeNotifications());
        
        // Initialize animations
        componentPromises.push(this.initializeAnimations());
        
        // Initialize performance optimizer
        componentPromises.push(this.initializePerformanceOptimizer());
        
        // Initialize interactivity
        componentPromises.push(this.initializeInteractivity());
        
        // Use Promise.allSettled to prevent one failed component from breaking everything
        const results = await Promise.allSettled(componentPromises);
        
        // Log results
        results.forEach((result, index) => {
            const componentNames = ['navigation', 'notifications', 'animations', 'performance', 'interactivity'];
            if (result.status === 'rejected') {
                console.warn(`Component ${componentNames[index]} initialization failed:`, result.reason);
            } else {
                console.log(`Component ${componentNames[index]} initialized successfully`);
            }
        });
        
        // Check if any critical components failed
        const failedComponents = results.filter(result => result.status === 'rejected').length;
        if (failedComponents > 0) {
            console.warn(`${failedComponents} components failed to initialize, but continuing with partial functionality`);
        }
    }
    
    async initializeNavigation() {
        try {
            if (!this.components.has('navigation')) {
                if (window.dashboardNavigation) {
                    this.components.set('navigation', window.dashboardNavigation);
                } else if (window.DashboardNavigation && typeof window.DashboardNavigation === 'function') {
                    this.components.set('navigation', new window.DashboardNavigation());
                } else {
                    console.warn('DashboardNavigation not available, skipping navigation initialization');
                    this.components.set('navigation', { initialized: false });
                }
            }
        } catch (error) {
            console.error('Navigation initialization failed:', error);
            this.components.set('navigation', { initialized: false, error: error.message });
        }
    }
    
    async initializeNotifications() {
        try {
            if (!this.components.has('notifications')) {
                if (window.notificationSystem) {
                    this.components.set('notifications', window.notificationSystem);
                } else if (window.NotificationSystem && typeof window.NotificationSystem === 'function') {
                    this.components.set('notifications', new window.NotificationSystem());
                } else {
                    console.warn('NotificationSystem not available, skipping notifications initialization');
                    this.components.set('notifications', { initialized: false });
                }
            }
        } catch (error) {
            console.error('Notifications initialization failed:', error);
            this.components.set('notifications', { initialized: false, error: error.message });
        }
    }
    
    async initializeAnimations() {
        try {
            if (!this.components.has('animations')) {
                if (window.dashboardAnimations) {
                    this.components.set('animations', window.dashboardAnimations);
                } else if (window.DashboardAnimations && typeof window.DashboardAnimations === 'function') {
                    this.components.set('animations', new window.DashboardAnimations());
                } else {
                    console.warn('DashboardAnimations not available, skipping animations initialization');
                    this.components.set('animations', { initialized: false });
                }
            }
        } catch (error) {
            console.error('Animations initialization failed:', error);
            this.components.set('animations', { initialized: false, error: error.message });
        }
    }
    
    async initializePerformanceOptimizer() {
        try {
            if (!this.components.has('performance')) {
                if (window.performanceOptimizer) {
                    this.components.set('performance', window.performanceOptimizer);
                } else if (window.PerformanceOptimizer && typeof window.PerformanceOptimizer === 'function') {
                    this.components.set('performance', new window.PerformanceOptimizer());
                } else {
                    console.warn('PerformanceOptimizer not available, skipping performance optimization initialization');
                    this.components.set('performance', { initialized: false });
                }
            }
        } catch (error) {
            console.error('Performance optimizer initialization failed:', error);
            this.components.set('performance', { initialized: false, error: error.message });
        }
    }
    
    async initializeInteractivity() {
        try {
            if (!this.components.has('interactivity')) {
                if (window.DashboardInteractivity) {
                    this.components.set('interactivity', window.DashboardInteractivity);
                } else {
                    console.warn('DashboardInteractivity not available, using fallback');
                    this.components.set('interactivity', { 
                        initialized: false,
                        showNotification: (message, type) => console.log(`Notification: ${message} (${type})`),
                        closeModal: (id) => console.log(`Modal closed: ${id}`)
                    });
                }
            }
        } catch (error) {
            console.error('Interactivity initialization failed:', error);
            this.components.set('interactivity', { 
                initialized: false, 
                error: error.message,
                showNotification: (message, type) => console.log(`Notification: ${message} (${type})`),
                closeModal: (id) => console.log(`Modal closed: ${id}`)
            });
        }
    }
    
    setupComponentCommunication() {
        // Create event bus for component communication
        this.eventBus = new EventTarget();
        
        // Setup component event listeners
        this.setupNavigationEvents();
        this.setupNotificationEvents();
        this.setupAnimationEvents();
        this.setupPerformanceEvents();
    }
    
    setupNavigationEvents() {
        // Listen for navigation events
        this.eventBus.addEventListener('navigation:change', (event) => {
            const { from, to } = event.detail;
            
            // Notify other components of navigation change
            this.components.get('animations')?.pageTransitionOut(() => {
                // Handle page transition
            });
            
            // Update notifications context
            this.components.get('notifications')?.updateContext(to);
        });
        
        // Listen for page load events
        window.addEventListener('load', () => {
            this.eventBus.dispatchEvent(new CustomEvent('page:loaded', {
                detail: { page: window.location.pathname }
            }));
        });
    }
    
    setupNotificationEvents() {
        // Listen for notification events
        this.eventBus.addEventListener('notification:new', (event) => {
            const notification = event.detail;
            
            // Add animation to notification
            this.components.get('animations')?.bounceIn(
                document.querySelector('.notification-badge')
            );
        });
        
        // Listen for notification interactions
        this.eventBus.addEventListener('notification:click', (event) => {
            const { notificationId, actionUrl } = event.detail;
            
            if (actionUrl) {
                // Use navigation component for smooth transitions
                this.components.get('navigation')?.navigateTo(actionUrl);
            }
        });
    }
    
    setupAnimationEvents() {
        // Listen for animation requests
        this.eventBus.addEventListener('animation:request', (event) => {
            const { element, type, options } = event.detail;
            const animations = this.components.get('animations');
            
            if (animations && animations[type]) {
                animations[type](element, options);
            }
        });
    }
    
    setupPerformanceEvents() {
        // Listen for performance events
        this.eventBus.addEventListener('performance:optimize', (event) => {
            const { type, target } = event.detail;
            const performance = this.components.get('performance');
            
            if (performance) {
                switch (type) {
                    case 'image':
                        performance.optimizeImage(target);
                        break;
                    case 'preload':
                        performance.preloadResource(target);
                        break;
                }
            }
        });
    }
    
    setupGlobalEventHandlers() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });
        
        // Global click tracking
        document.addEventListener('click', (e) => {
            this.handleGlobalClick(e);
        });
        
        // Global error handling
        window.addEventListener('error', (e) => {
            this.handleGlobalError(e);
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            this.handleUnhandledRejection(e);
        });
        
        // Visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Online/offline status
        window.addEventListener('online', () => {
            this.handleOnlineStatus(true);
        });
        
        window.addEventListener('offline', () => {
            this.handleOnlineStatus(false);
        });
    }
    
    setupAccessibility() {
        // Skip to main content link
        this.createSkipLink();
        
        // Focus management
        this.setupFocusManagement();
        
        // ARIA live regions
        this.setupLiveRegions();
        
        // High contrast mode detection
        this.setupHighContrastMode();
        
        // Reduced motion detection
        this.setupReducedMotion();
    }
    
    setupErrorHandling() {
        // Component error boundaries
        this.setupComponentErrorBoundaries();
        
        // Network error handling
        this.setupNetworkErrorHandling();
        
        // User-friendly error messages
        this.setupUserErrorMessages();
    }
    
    setupComponentErrorBoundaries() {
        // Setup error boundaries for components
        this.components.forEach((component, name) => {
            if (component && typeof component.on === 'function') {
                component.on('error', (error) => {
                    console.error(`Component ${name} error:`, error);
                    this.handleComponentError(name, error);
                });
            }
        });
    }
    
    setupNetworkErrorHandling() {
        // Handle network errors
        window.addEventListener('online', () => {
            this.showMessage('Connection restored', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.showMessage('You are offline', 'warning');
        });
    }
    
    setupUserErrorMessages() {
        // Setup user-friendly error messages
        this.errorMessages = {
            network: 'Network connection error. Please check your internet connection.',
            timeout: 'Request timed out. Please try again.',
            server: 'Server error. Please try again later.',
            generic: 'Something went wrong. Please try again.'
        };
    }
    
    handleComponentError(componentName, error) {
        // Handle component-specific errors
        const errorMessage = this.getErrorMessage(error);
        this.showMessage(errorMessage, 'error');
        
        // Try to recover the component
        this.recoverComponent(componentName);
    }
    
    getErrorMessage(error) {
        if (error.message.includes('network')) {
            return this.errorMessages.network;
        } else if (error.message.includes('timeout')) {
            return this.errorMessages.timeout;
        } else if (error.message.includes('server')) {
            return this.errorMessages.server;
        }
        return this.errorMessages.generic;
    }
    
    recoverComponent(componentName) {
        // Attempt to recover a failed component
        setTimeout(() => {
            try {
                const component = this.components.get(componentName);
                if (component && typeof component.initialize === 'function') {
                    component.initialize();
                }
            } catch (error) {
                console.error(`Failed to recover component ${componentName}:`, error);
            }
        }, 1000);
    }
    
    finalOptimizations() {
        // Remove unused CSS
        this.removeUnusedCSS();
        
        // Optimize images
        this.optimizeImages();
        
        // Setup lazy loading
        this.setupLazyLoading();
        
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Setup service worker
        this.setupServiceWorker();
    }
    
    // Event handlers
    handleGlobalKeyboard(e) {
        // Global keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case '/':
                    e.preventDefault();
                    this.focusSearch();
                    break;
                case 'k':
                    e.preventDefault();
                    this.openCommandPalette();
                    break;
            }
        }
        
        // Escape key handling
        if (e.key === 'Escape') {
            this.handleEscapeKey();
        }
    }
    
    handleGlobalClick(e) {
        // Track user interactions
        this.trackInteraction('click', e.target);
        
        // Handle special click behaviors
        if (e.target.matches('[data-track]')) {
            this.trackCustomEvent(e.target.dataset.track, e.target);
        }
    }
    
    handleGlobalError(e) {
        console.error('Global error:', e.error);
        
        // Report error to monitoring service
        this.reportError(e.error);
        
        // Show user-friendly error message
        this.showErrorMessage('Something went wrong. Please try again.');
    }
    
    handleUnhandledRejection(e) {
        console.error('Unhandled promise rejection:', e.reason);
        
        // Report error
        this.reportError(e.reason);
        
        // Prevent default browser behavior
        e.preventDefault();
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden - pause non-critical operations
            this.pauseNonCriticalOperations();
        } else {
            // Page is visible - resume operations
            this.resumeOperations();
        }
    }
    
    handleOnlineStatus(isOnline) {
        if (isOnline) {
            this.showMessage('Connection restored', 'success');
            this.syncOfflineData();
        } else {
            this.showMessage('You are offline', 'warning');
            this.enableOfflineMode();
        }
    }
    
    // Accessibility methods
    createSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded';
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
    
    setupFocusManagement() {
        // Focus trap for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal:not(.hidden)');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }
    
    setupLiveRegions() {
        // Create ARIA live regions for dynamic content
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        
        document.body.appendChild(liveRegion);
    }
    
    setupHighContrastMode() {
        // Detect high contrast mode
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            document.body.classList.add('high-contrast');
        }
    }
    
    setupReducedMotion() {
        // Detect reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
            
            // Disable animations
            const animations = this.components.get('animations');
            if (animations) {
                animations.destroy();
            }
        }
    }
    
    // Performance monitoring
    startPerformanceMonitoring() {
        // Core Web Vitals
        this.monitorCoreWebVitals();
        
        // Custom metrics
        this.monitorCustomMetrics();
        
        // Resource timing
        this.monitorResourceTiming();
    }
    
    monitorCoreWebVitals() {
        // Implementation would use web-vitals library or similar
        console.log('Monitoring Core Web Vitals...');
    }
    
    monitorCustomMetrics() {
        // Track custom performance metrics
        this.performanceMetrics.initTime = performance.now();
    }
    
    monitorResourceTiming() {
        // Monitor resource loading performance
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.duration > 1000) {
                        console.warn('Slow resource:', entry.name, entry.duration);
                    }
                });
            });
            
            observer.observe({ entryTypes: ['resource'] });
        }
    }
    
    // Utility methods
    focusSearch() {
        const searchInput = document.querySelector('#globalSearch, [data-search]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    openCommandPalette() {
        // Implementation for command palette
        console.log('Opening command palette...');
    }
    
    handleEscapeKey() {
        // Close any open modals or dropdowns
        const openModal = document.querySelector('.modal:not(.hidden)');
        if (openModal) {
            this.components.get('interactivity')?.closeModal(openModal.id);
        }
        
        const openDropdown = document.querySelector('.dropdown.show');
        if (openDropdown) {
            openDropdown.classList.remove('show');
        }
    }
    
    trackInteraction(type, element) {
        // Track user interactions for analytics
        const data = {
            type,
            element: element.tagName,
            className: element.className,
            timestamp: Date.now()
        };
        
        // Store in analytics queue
        this.addToAnalyticsQueue(data);
    }
    
    trackCustomEvent(eventName, element) {
        // Track custom events
        console.log('Custom event:', eventName, element);
    }
    
    reportError(error) {
        // Report errors to monitoring service
        console.error('Reporting error:', error);
    }
    
    showErrorMessage(message) {
        // Show user-friendly error message
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type = 'info') {
        // Show toast message
        const interactivity = this.components.get('interactivity');
        if (interactivity && interactivity.showNotification) {
            interactivity.showNotification(message, type);
        }
    }
    
    pauseNonCriticalOperations() {
        // Pause animations, polling, etc.
        console.log('Pausing non-critical operations');
    }
    
    resumeOperations() {
        // Resume paused operations
        console.log('Resuming operations');
    }
    
    syncOfflineData() {
        // Sync any offline data when connection is restored
        console.log('Syncing offline data');
    }
    
    enableOfflineMode() {
        // Enable offline functionality
        console.log('Enabling offline mode');
    }
    
    trapFocus(e, container) {
        // Focus trap implementation
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
    
    addToAnalyticsQueue(data) {
        // Add to analytics queue for batch sending
        const queue = JSON.parse(localStorage.getItem('analyticsQueue') || '[]');
        queue.push(data);
        
        // Keep only last 100 events
        if (queue.length > 100) {
            queue.shift();
        }
        
        localStorage.setItem('analyticsQueue', JSON.stringify(queue));
    }
    
    dispatchReadyEvent() {
        // Dispatch custom ready event
        const event = new CustomEvent('dashboard:ready', {
            detail: {
                components: Array.from(this.components.keys()),
                performanceMetrics: this.performanceMetrics
            }
        });
        
        document.dispatchEvent(event);
    }
    
    isCriticalError(error) {
        // In safe mode, don't show error UI
        if (this.safeMode) {
            return false;
        }
        
        // Don't show error UI if we've already tried multiple times
        if (this.initializationAttempts > this.maxInitializationAttempts) {
            return false;
        }
        
        // Determine if an error is critical enough to show fallback UI
        const criticalErrors = [
            'ReferenceError',
            'SyntaxError',
            'TypeError: Cannot read properties of undefined',
            'TypeError: Cannot read properties of null'
        ];
        
        // Check if error message contains critical error patterns
        const errorMessage = error.message || error.toString();
        const isCritical = criticalErrors.some(criticalError => 
            errorMessage.includes(criticalError) || error.name === criticalError
        );
        
        // Also consider errors that prevent basic functionality
        const preventsFunctionality = errorMessage.includes('EventTarget') || 
                                    errorMessage.includes('addEventListener') ||
                                    errorMessage.includes('document is not defined');
        
        return isCritical || preventsFunctionality;
    }
    
    handleInitializationError(error) {
        // Handle initialization errors gracefully
        document.body.classList.add('dashboard-error');
        
        // Show fallback UI
        this.showFallbackUI(error);
    }
    
    showFallbackUI(error) {
        // Track reload attempts
        const reloadCount = parseInt(sessionStorage.getItem('dashboardReloadCount') || '0') + 1;
        sessionStorage.setItem('dashboardReloadCount', reloadCount.toString());
        
        // Show minimal fallback UI
        const fallback = document.createElement('div');
        fallback.className = 'fixed inset-0 bg-gray-50 flex items-center justify-center z-50';
        fallback.innerHTML = `
            <div class="text-center p-8 max-w-md">
                <h1 class="text-2xl font-bold text-gray-900 mb-4">Dashboard Loading Error</h1>
                <p class="text-gray-600 mb-4">There was an error loading the dashboard.</p>
                <div class="space-y-2 mb-4">
                    <button onclick="window.dashboardIntegration?.reinitialize()" class="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                        Try Again
                    </button>
                    <button onclick="window.location.reload()" class="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        Refresh Page
                    </button>
                    ${reloadCount > 1 ? `
                    <button onclick="sessionStorage.clear(); window.location.reload()" class="w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">
                        Clear Cache & Refresh
                    </button>
                    ` : ''}
                </div>
                <details class="text-left">
                    <summary class="cursor-pointer text-sm text-gray-500 hover:text-gray-700">Error Details</summary>
                    <pre class="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">${error.stack || error.message || error}</pre>
                </details>
            </div>
        `;
        
        document.body.appendChild(fallback);
    }
    
    // Optimization methods
    removeUnusedCSS() {
        // Remove unused CSS rules to improve performance
        try {
            const usedSelectors = new Set();
            const allElements = document.querySelectorAll('*');
            
            // Collect all used classes and IDs
            allElements.forEach(element => {
                if (element.className) {
                    const classes = element.className.toString().split(' ');
                    classes.forEach(cls => {
                        if (cls.trim()) {
                            usedSelectors.add(`.${cls.trim()}`);
                        }
                    });
                }
                if (element.id) {
                    usedSelectors.add(`#${element.id}`);
                }
            });
            
            // Note: In a real implementation, you would analyze stylesheets
            // and remove unused rules. This is a simplified version.
            console.log('CSS optimization completed. Used selectors:', usedSelectors.size);
            
        } catch (error) {
            console.warn('CSS optimization failed:', error);
        }
    }
    
    optimizeImages() {
        // Optimize images for better performance
        try {
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                // Add loading="lazy" if not already present
                if (!img.hasAttribute('loading')) {
                    img.setAttribute('loading', 'lazy');
                }
                
                // Add decoding="async" for better performance
                if (!img.hasAttribute('decoding')) {
                    img.setAttribute('decoding', 'async');
                }
                
                // Optimize image dimensions
                if (img.naturalWidth && img.naturalHeight) {
                    const displayWidth = img.offsetWidth;
                    const displayHeight = img.offsetHeight;
                    
                    // If image is much larger than display size, suggest optimization
                    if (img.naturalWidth > displayWidth * 2 || img.naturalHeight > displayHeight * 2) {
                        console.warn('Image could be optimized:', img.src, {
                            natural: { width: img.naturalWidth, height: img.naturalHeight },
                            display: { width: displayWidth, height: displayHeight }
                        });
                    }
                }
            });
            
            console.log('Image optimization completed for', images.length, 'images');
            
        } catch (error) {
            console.warn('Image optimization failed:', error);
        }
    }
    
    setupLazyLoading() {
        // Setup lazy loading for various elements
        try {
            // Lazy load images that don't already have it
            const images = document.querySelectorAll('img:not([loading])');
            images.forEach(img => {
                img.setAttribute('loading', 'lazy');
            });
            
            // Setup intersection observer for custom lazy loading
            if ('IntersectionObserver' in window) {
                const lazyElements = document.querySelectorAll('[data-lazy]');
                
                if (lazyElements.length > 0) {
                    const lazyObserver = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                const element = entry.target;
                                const src = element.dataset.lazy;
                                
                                if (element.tagName === 'IMG') {
                                    element.src = src;
                                } else if (element.tagName === 'IFRAME') {
                                    element.src = src;
                                }
                                
                                element.removeAttribute('data-lazy');
                                lazyObserver.unobserve(element);
                            }
                        });
                    }, {
                        rootMargin: '50px 0px',
                        threshold: 0.01
                    });
                    
                    lazyElements.forEach(element => {
                        lazyObserver.observe(element);
                    });
                }
            }
            
            console.log('Lazy loading setup completed');
            
        } catch (error) {
            console.warn('Lazy loading setup failed:', error);
        }
    }
    
    preloadCriticalResources() {
        // Preload critical resources for better performance
        try {
            const criticalResources = [
                { href: '/static/css/dashboard-integration.css', as: 'style' },
                { href: '/static/js/dashboard-navigation.js', as: 'script' },
                { href: '/static/js/notifications.js', as: 'script' }
            ];
            
            criticalResources.forEach(resource => {
                // Check if already preloaded
                const existing = document.querySelector(`link[rel="preload"][href="${resource.href}"]`);
                if (!existing) {
                    const link = document.createElement('link');
                    link.rel = 'preload';
                    link.href = resource.href;
                    link.as = resource.as;
                    if (resource.type) link.type = resource.type;
                    document.head.appendChild(link);
                }
            });
            
            // Preload likely next pages
            const navigationLinks = document.querySelectorAll('a[href^="/insurance/"]');
            const preloadedUrls = new Set();
            
            navigationLinks.forEach(link => {
                link.addEventListener('mouseenter', () => {
                    const url = link.href;
                    if (!preloadedUrls.has(url)) {
                        preloadedUrls.add(url);
                        const prefetchLink = document.createElement('link');
                        prefetchLink.rel = 'prefetch';
                        prefetchLink.href = url;
                        document.head.appendChild(prefetchLink);
                    }
                }, { once: true });
            });
            
            console.log('Critical resources preloading setup completed');
            
        } catch (error) {
            console.warn('Critical resources preloading failed:', error);
        }
    }
    
    setupServiceWorker() {
        // Setup service worker for caching and offline functionality
        try {
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/static/js/sw.js')
                    .then(registration => {
                        console.log('Service Worker registered successfully:', registration.scope);
                        
                        // Listen for updates
                        registration.addEventListener('updatefound', () => {
                            const newWorker = registration.installing;
                            if (newWorker) {
                                newWorker.addEventListener('statechange', () => {
                                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                        // New version available
                                        this.showUpdateAvailable();
                                    }
                                });
                            }
                        });
                    })
                    .catch(error => {
                        console.warn('Service Worker registration failed:', error);
                    });
            } else {
                console.log('Service Worker not supported');
            }
        } catch (error) {
            console.warn('Service Worker setup failed:', error);
        }
    }
    
    showUpdateAvailable() {
        // Show update notification to user
        const updateBanner = document.createElement('div');
        updateBanner.className = 'fixed top-0 left-0 right-0 bg-blue-600 text-white p-3 text-center z-50';
        updateBanner.innerHTML = `
            <span>A new version is available!</span>
            <button onclick="window.location.reload()" class="ml-4 bg-blue-700 px-3 py-1 rounded text-sm hover:bg-blue-800">
                Update Now
            </button>
            <button onclick="this.parentElement.remove()" class="ml-2 text-blue-200 hover:text-white">
                ×
            </button>
        `;
        document.body.insertBefore(updateBanner, document.body.firstChild);
    }
    
    // Public API
    getComponent(name) {
        return this.components.get(name);
    }
    
    isInitialized() {
        return this.initialized;
    }
    
    getPerformanceMetrics() {
        return { ...this.performanceMetrics };
    }
    
    emit(eventName, detail) {
        this.eventBus.dispatchEvent(new CustomEvent(eventName, { detail }));
    }
    
    on(eventName, handler) {
        this.eventBus.addEventListener(eventName, handler);
    }
    
    off(eventName, handler) {
        this.eventBus.removeEventListener(eventName, handler);
    }
    
    // Utility methods for debugging and recovery
    reinitialize() {
        console.log('🔄 Reinitializing Dashboard Integration...');
        this.initialized = false;
        this.components.clear();
        
        // Remove any existing error UI
        const existingError = document.querySelector('.dashboard-error');
        if (existingError) {
            document.body.classList.remove('dashboard-error');
            const fallbackUI = document.querySelector('.fixed.inset-0.bg-gray-50');
            if (fallbackUI) {
                fallbackUI.remove();
            }
        }
        
        // Reinitialize
        this.initialize();
    }
    
    getStatus() {
        return {
            initialized: this.initialized,
            components: Array.from(this.components.keys()),
            componentStatus: Object.fromEntries(
                Array.from(this.components.entries()).map(([name, component]) => [
                    name, 
                    component.initialized !== undefined ? component.initialized : true
                ])
            ),
            performanceMetrics: this.performanceMetrics
        };
    }
}

// Initialize dashboard integration (only if not already initialized)
if (!window.dashboardIntegration) {
    window.dashboardIntegration = new DashboardIntegration();
} else {
    console.log('Dashboard integration already initialized, skipping...');
}

// Export for external use
window.DashboardIntegration = DashboardIntegration;

// Global ready state
window.addEventListener('load', () => {
    console.log('🎉 Dashboard fully loaded and ready!');
});