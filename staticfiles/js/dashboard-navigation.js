/**
 * Dashboard Navigation JavaScript
 * Handles consistent navigation and integration between dashboard pages
 */

class DashboardNavigation {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.navigationHistory = [];
        this.breadcrumbs = [];
        
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.setupBreadcrumbs();
        this.setupPageTransitions();
        this.setupKeyboardShortcuts();
        this.trackNavigation();
    }
    
    getCurrentPage() {
        const path = window.location.pathname;
        
        if (path.includes('/assessments/')) {
            return 'assessment_dashboard';
        } else if (path.includes('/book-assessment/')) {
            return 'booking';
        } else if (path.includes('/insurance/')) {
            return 'landing';
        }
        
        return 'unknown';
    }
    
    setupNavigation() {
        // Update active navigation states
        this.updateActiveNavigation();
        
        // Setup navigation event listeners
        const navLinks = document.querySelectorAll('.nav-item, .mobile-nav-item');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.handleNavigation(e, link);
            });
        });
        
        // Setup action card navigation
        const actionCards = document.querySelectorAll('.action-card[data-url]');
        actionCards.forEach(card => {
            card.addEventListener('click', (e) => {
                this.handleCardNavigation(e, card);
            });
        });
    }
    
    updateActiveNavigation() {
        // Remove all active states
        document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(item => {
            item.classList.remove('active', 'text-primary', 'bg-blue-50');
        });
        
        // Add active state to current page
        const currentNavItem = document.querySelector(`[href*="${this.getPagePath()}"]`);
        if (currentNavItem) {
            currentNavItem.classList.add('active', 'text-primary');
            if (currentNavItem.classList.contains('mobile-nav-item')) {
                currentNavItem.classList.add('bg-blue-50');
            }
        }
    }
    
    getPagePath() {
        const paths = {
            'landing': '/insurance/',
            'assessment_dashboard': '/assessments/',
            'booking': '/book-assessment/'
        };
        
        return paths[this.currentPage] || '/insurance/';
    }
    
    setupBreadcrumbs() {
        const breadcrumbData = this.getBreadcrumbData();
        this.renderBreadcrumbs(breadcrumbData);
    }
    
    getBreadcrumbData() {
        const breadcrumbs = {
            'landing': [
                { text: 'Home', url: '/insurance/', icon: 'fas fa-home' }
            ],
            'assessment_dashboard': [
                { text: 'Home', url: '/insurance/', icon: 'fas fa-home' },
                { text: 'Assessment Dashboard', url: '/insurance/assessments/', icon: 'fas fa-chart-line' }
            ],
            'booking': [
                { text: 'Home', url: '/insurance/', icon: 'fas fa-home' },
                { text: 'Book New Assessment', url: '/insurance/book-assessment/', icon: 'fas fa-plus-circle' }
            ]
        };
        
        return breadcrumbs[this.currentPage] || breadcrumbs['landing'];
    }
    
    renderBreadcrumbs(breadcrumbData) {
        const breadcrumbContainer = document.querySelector('.breadcrumb-list, nav[aria-label="Breadcrumb"] ol');
        if (!breadcrumbContainer) return;
        
        breadcrumbContainer.innerHTML = '';
        
        breadcrumbData.forEach((crumb, index) => {
            const isLast = index === breadcrumbData.length - 1;
            
            // Create breadcrumb item
            const listItem = document.createElement('li');
            
            if (isLast) {
                listItem.innerHTML = `
                    <div class="flex items-center">
                        ${index > 0 ? '<i class="fas fa-chevron-right text-gray-300 mr-4"></i>' : ''}
                        <span class="text-sm font-medium text-gray-900">${crumb.text}</span>
                    </div>
                `;
            } else {
                listItem.innerHTML = `
                    <div class="flex items-center">
                        <a href="${crumb.url}" class="text-gray-400 hover:text-gray-500 transition-colors duration-200">
                            <i class="${crumb.icon}"></i>
                            <span class="sr-only">${crumb.text}</span>
                        </a>
                    </div>
                `;
            }
            
            breadcrumbContainer.appendChild(listItem);
        });
    }
    
    setupPageTransitions() {
        // Add loading states for navigation
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.isInternalLink(link.href)) {
                this.showNavigationLoading();
            }
        });
        
        // Hide loading when page loads
        window.addEventListener('load', () => {
            this.hideNavigationLoading();
        });
    }
    
    isInternalLink(href) {
        return href.includes('/insurance/') && !href.includes('http');
    }
    
    showNavigationLoading() {
        // Create or show loading overlay
        let loadingOverlay = document.getElementById('navigationLoading');
        
        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'navigationLoading';
            loadingOverlay.className = 'fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50';
            loadingOverlay.innerHTML = `
                <div class="text-center">
                    <div class="loading-spinner mx-auto mb-4"></div>
                    <p class="text-gray-600">Loading...</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        }
        
        loadingOverlay.style.display = 'flex';
    }
    
    hideNavigationLoading() {
        const loadingOverlay = document.getElementById('navigationLoading');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }
    
    handleNavigation(e, link) {
        const href = link.getAttribute('href');
        
        if (href && this.isInternalLink(href)) {
            // Add navigation tracking
            this.trackNavigationClick(href, link.textContent.trim());
            
            // Add visual feedback
            link.style.transform = 'scale(0.98)';
            setTimeout(() => {
                link.style.transform = '';
            }, 150);
        }
    }
    
    handleCardNavigation(e, card) {
        const url = card.getAttribute('data-url');
        
        if (url) {
            // Add click animation
            card.style.transform = 'scale(0.98)';
            
            // Track navigation
            this.trackNavigationClick(url, 'Action Card');
            
            // Navigate after animation
            setTimeout(() => {
                window.location.href = url;
            }, 150);
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts when not in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            if (e.altKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.navigateTo('/insurance/');
                        break;
                    case '2':
                        e.preventDefault();
                        this.navigateTo('/insurance/assessments/');
                        break;
                    case '3':
                        e.preventDefault();
                        this.navigateTo('/insurance/book-assessment/');
                        break;
                }
            }
            
            // Escape key to go back to landing
            if (e.key === 'Escape' && this.currentPage !== 'landing') {
                e.preventDefault();
                this.navigateTo('/insurance/');
            }
        });
    }
    
    navigateTo(url) {
        this.showNavigationLoading();
        window.location.href = url;
    }
    
    trackNavigation() {
        // Track page view
        this.trackPageView();
        
        // Track time spent on page
        this.startTimeTracking();
    }
    
    trackPageView() {
        const pageData = {
            page: this.currentPage,
            url: window.location.pathname,
            timestamp: new Date().toISOString(),
            referrer: document.referrer
        };
        
        // Store in localStorage for analytics
        const navigationHistory = JSON.parse(localStorage.getItem('navigationHistory') || '[]');
        navigationHistory.push(pageData);
        
        // Keep only last 50 entries
        if (navigationHistory.length > 50) {
            navigationHistory.shift();
        }
        
        localStorage.setItem('navigationHistory', JSON.stringify(navigationHistory));
    }
    
    trackNavigationClick(url, linkText) {
        const clickData = {
            from: this.currentPage,
            to: url,
            linkText: linkText,
            timestamp: new Date().toISOString()
        };
        
        // Store click tracking
        const clickHistory = JSON.parse(localStorage.getItem('clickHistory') || '[]');
        clickHistory.push(clickData);
        
        // Keep only last 100 entries
        if (clickHistory.length > 100) {
            clickHistory.shift();
        }
        
        localStorage.setItem('clickHistory', JSON.stringify(clickHistory));
    }
    
    startTimeTracking() {
        this.pageStartTime = Date.now();
        
        // Track time when leaving page
        window.addEventListener('beforeunload', () => {
            const timeSpent = Date.now() - this.pageStartTime;
            
            const timeData = {
                page: this.currentPage,
                timeSpent: timeSpent,
                timestamp: new Date().toISOString()
            };
            
            // Store time tracking
            const timeHistory = JSON.parse(localStorage.getItem('timeHistory') || '[]');
            timeHistory.push(timeData);
            
            // Keep only last 50 entries
            if (timeHistory.length > 50) {
                timeHistory.shift();
            }
            
            localStorage.setItem('timeHistory', JSON.stringify(timeHistory));
        });
    }
    
    // Public methods for external use
    goToLanding() {
        this.navigateTo('/insurance/');
    }
    
    goToAssessments() {
        this.navigateTo('/insurance/assessments/');
    }
    
    goToBooking() {
        this.navigateTo('/insurance/book-assessment/');
    }
    
    getNavigationHistory() {
        return JSON.parse(localStorage.getItem('navigationHistory') || '[]');
    }
    
    getClickHistory() {
        return JSON.parse(localStorage.getItem('clickHistory') || '[]');
    }
    
    getTimeHistory() {
        return JSON.parse(localStorage.getItem('timeHistory') || '[]');
    }
    
    clearHistory() {
        localStorage.removeItem('navigationHistory');
        localStorage.removeItem('clickHistory');
        localStorage.removeItem('timeHistory');
    }
}

// Page-specific enhancements
class PageEnhancements {
    constructor() {
        this.currentPage = window.dashboardNavigation?.currentPage || 'unknown';
        this.init();
    }
    
    init() {
        this.setupPageSpecificFeatures();
        this.setupCrossPlatformIntegration();
        this.setupPerformanceOptimizations();
    }
    
    setupPageSpecificFeatures() {
        switch(this.currentPage) {
            case 'landing':
                this.enhanceLandingPage();
                break;
            case 'assessment_dashboard':
                this.enhanceAssessmentDashboard();
                break;
            case 'booking':
                this.enhanceBookingPage();
                break;
        }
    }
    
    enhanceLandingPage() {
        // Add hover effects to action cards
        const actionCards = document.querySelectorAll('.action-card');
        actionCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
        
        // Add quick stats animation
        this.animateQuickStats();
    }
    
    enhanceAssessmentDashboard() {
        // Add KPI card interactions
        const kpiCards = document.querySelectorAll('.kpi-card');
        kpiCards.forEach(card => {
            card.addEventListener('click', () => {
                this.showKPIDetails(card);
            });
        });
        
        // Setup real-time updates
        this.setupRealTimeUpdates();
    }
    
    enhanceBookingPage() {
        // Add form progress tracking
        this.setupFormProgress();
        
        // Add file upload enhancements
        this.enhanceFileUpload();
    }
    
    animateQuickStats() {
        const statsCards = document.querySelectorAll('.stats-card, [class*="stats"]');
        
        statsCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });
    }
    
    showKPIDetails(card) {
        // Create modal or tooltip with detailed KPI information
        const kpiType = card.querySelector('.text-xs')?.textContent || 'KPI';
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold mb-4">${kpiType} Details</h3>
                <p class="text-gray-600 mb-4">Detailed information about this KPI would be displayed here.</p>
                <button class="action-button action-button-primary" onclick="this.closest('.fixed').remove()">
                    Close
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    setupRealTimeUpdates() {
        // Simulate real-time updates for demo purposes
        setInterval(() => {
            this.updateKPIValues();
        }, 30000); // Update every 30 seconds
    }
    
    updateKPIValues() {
        const kpiValues = document.querySelectorAll('.kpi-card .text-2xl');
        
        kpiValues.forEach(value => {
            const currentValue = parseInt(value.textContent);
            if (!isNaN(currentValue)) {
                // Simulate small changes
                const change = Math.floor(Math.random() * 3) - 1; // -1, 0, or 1
                const newValue = Math.max(0, currentValue + change);
                
                if (newValue !== currentValue) {
                    value.textContent = newValue;
                    value.classList.add('bounce-in');
                    setTimeout(() => {
                        value.classList.remove('bounce-in');
                    }, 600);
                }
            }
        });
    }
    
    setupFormProgress() {
        const form = document.querySelector('form[data-validate]');
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, select, textarea');
        const progressBar = document.querySelector('#progressBar');
        
        if (progressBar) {
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    this.updateFormProgress(form, progressBar);
                });
            });
        }
    }
    
    updateFormProgress(form, progressBar) {
        const inputs = form.querySelectorAll('input, select, textarea');
        const filledInputs = Array.from(inputs).filter(input => input.value.trim() !== '');
        const progress = (filledInputs.length / inputs.length) * 100;
        
        progressBar.style.width = `${progress}%`;
    }
    
    enhanceFileUpload() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;
        
        // Add drag and drop visual feedback
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            this.handleFileUpload(files);
        });
    }
    
    handleFileUpload(files) {
        Array.from(files).forEach(file => {
            console.log('Uploading file:', file.name);
            // File upload logic would go here
        });
    }
    
    setupCrossPlatformIntegration() {
        // Setup data sharing between pages
        this.setupDataCache();
        
        // Setup consistent user preferences
        this.loadUserPreferences();
    }
    
    setupDataCache() {
        // Cache frequently used data
        const cacheKey = `dashboard_cache_${this.currentPage}`;
        const cachedData = localStorage.getItem(cacheKey);
        
        if (cachedData) {
            try {
                const data = JSON.parse(cachedData);
                this.applyCachedData(data);
            } catch (e) {
                console.warn('Failed to parse cached data:', e);
            }
        }
    }
    
    applyCachedData(data) {
        // Apply cached data to current page
        if (data.userPreferences) {
            this.applyUserPreferences(data.userPreferences);
        }
    }
    
    loadUserPreferences() {
        const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
        this.applyUserPreferences(preferences);
    }
    
    applyUserPreferences(preferences) {
        // Apply theme preferences
        if (preferences.theme) {
            document.body.classList.add(`theme-${preferences.theme}`);
        }
        
        // Apply notification preferences
        if (preferences.notifications === false) {
            // Disable notifications
        }
    }
    
    setupPerformanceOptimizations() {
        // Lazy load images
        this.setupLazyLoading();
        
        // Preload critical resources
        this.preloadCriticalResources();
    }
    
    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('loading-skeleton');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => {
                img.src = img.dataset.src;
            });
        }
    }
    
    preloadCriticalResources() {
        const criticalPages = [
            '/insurance/',
            '/insurance/assessments/',
            '/insurance/book-assessment/'
        ];
        
        criticalPages.forEach(page => {
            if (page !== window.location.pathname) {
                const link = document.createElement('link');
                link.rel = 'prefetch';
                link.href = page;
                document.head.appendChild(link);
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardNavigation = new DashboardNavigation();
    window.pageEnhancements = new PageEnhancements();
});

// Export for external use
window.DashboardNavigation = DashboardNavigation;
window.PageEnhancements = PageEnhancements;