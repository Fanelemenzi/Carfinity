/**
 * Accessibility Enhancements for AutoCare Dashboard
 * Implements ARIA labels, semantic HTML structure, keyboard navigation, and color contrast compliance
 */

class AccessibilityEnhancements {
    constructor() {
        this.isInitialized = false;
        this.focusableElements = [];
        this.currentFocusIndex = -1;
        this.announcements = [];
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupAriaLabels();
        this.setupSemanticStructure();
        this.setupKeyboardNavigation();
        this.setupScreenReaderSupport();
        this.setupFocusManagement();
        this.setupColorContrastCompliance();
        this.setupAccessibilityShortcuts();
        this.setupLiveRegions();
        
        this.isInitialized = true;
        console.log('Accessibility enhancements initialized');
    }
    
    setupAriaLabels() {
        // Add ARIA labels to interactive elements without proper labels
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
        
        interactiveElements.forEach(element => {
            this.addAriaLabelsToElement(element);
        });
        
        // Add ARIA labels to navigation elements
        this.setupNavigationAriaLabels();
        
        // Add ARIA labels to form elements
        this.setupFormAriaLabels();
        
        // Add ARIA labels to dashboard components
        this.setupDashboardAriaLabels();
    }
    
    addAriaLabelsToElement(element) {
        // Skip if element already has proper labeling
        if (element.getAttribute('aria-label') || 
            element.getAttribute('aria-labelledby') || 
            element.getAttribute('title') ||
            element.querySelector('span:not(.sr-only)')) {
            return;
        }
        
        const tagName = element.tagName.toLowerCase();
        const className = element.className;
        const iconClass = element.querySelector('i')?.className || '';
        
        // Generate appropriate ARIA label based on context
        let ariaLabel = '';
        
        if (iconClass.includes('fa-bars')) {
            ariaLabel = 'Open navigation menu';
        } else if (iconClass.includes('fa-times')) {
            ariaLabel = 'Close navigation menu';
        } else if (iconClass.includes('fa-bell')) {
            ariaLabel = 'View notifications';
        } else if (iconClass.includes('fa-user')) {
            ariaLabel = 'User profile menu';
        } else if (iconClass.includes('fa-chevron-down')) {
            ariaLabel = 'Expand dropdown menu';
        } else if (iconClass.includes('fa-car')) {
            ariaLabel = 'Vehicle information';
        } else if (iconClass.includes('fa-wrench')) {
            ariaLabel = 'Maintenance tools';
        } else if (iconClass.includes('fa-history')) {
            ariaLabel = 'Service history';
        } else if (iconClass.includes('fa-chart-line')) {
            ariaLabel = 'Analytics dashboard';
        } else if (iconClass.includes('fa-cog')) {
            ariaLabel = 'Settings';
        } else if (iconClass.includes('fa-sign-out-alt')) {
            ariaLabel = 'Sign out';
        } else if (className.includes('vehicle-selector')) {
            ariaLabel = 'Select vehicle';
        } else if (className.includes('notification')) {
            ariaLabel = 'Notification item';
        } else if (tagName === 'button' && element.textContent.trim()) {
            ariaLabel = element.textContent.trim();
        } else if (tagName === 'a' && element.textContent.trim()) {
            ariaLabel = element.textContent.trim();
        } else {
            // Generic fallback
            ariaLabel = `${tagName} element`;
        }
        
        if (ariaLabel) {
            element.setAttribute('aria-label', ariaLabel);
        }
    }
    
    setupNavigationAriaLabels() {
        // Main navigation
        const mainNav = document.querySelector('nav, .navigation, header nav');
        if (mainNav) {
            mainNav.setAttribute('role', 'navigation');
            mainNav.setAttribute('aria-label', 'Main navigation');
        }
        
        // Mobile navigation
        const mobileNav = document.getElementById('mobile-nav');
        if (mobileNav) {
            mobileNav.setAttribute('role', 'navigation');
            mobileNav.setAttribute('aria-label', 'Mobile navigation menu');
            mobileNav.setAttribute('aria-hidden', 'true');
        }
        
        // Navigation links
        const navLinks = document.querySelectorAll('nav a, .nav-item');
        navLinks.forEach(link => {
            if (!link.getAttribute('aria-label') && link.textContent.trim()) {
                link.setAttribute('aria-label', `Navigate to ${link.textContent.trim()}`);
            }
        });
        
        // Breadcrumbs if present
        const breadcrumbs = document.querySelector('.breadcrumb, [aria-label*="breadcrumb"]');
        if (breadcrumbs) {
            breadcrumbs.setAttribute('role', 'navigation');
            breadcrumbs.setAttribute('aria-label', 'Breadcrumb navigation');
        }
    }
    
    setupFormAriaLabels() {
        // Form controls
        const formControls = document.querySelectorAll('input, select, textarea');
        formControls.forEach(control => {
            const label = document.querySelector(`label[for="${control.id}"]`);
            const placeholder = control.getAttribute('placeholder');
            
            if (!label && !control.getAttribute('aria-label') && placeholder) {
                control.setAttribute('aria-label', placeholder);
            }
            
            // Add required indicator
            if (control.hasAttribute('required')) {
                const currentLabel = control.getAttribute('aria-label') || '';
                control.setAttribute('aria-label', `${currentLabel} (required)`.trim());
                control.setAttribute('aria-required', 'true');
            }
        });
        
        // Form validation messages
        const errorMessages = document.querySelectorAll('.error-message, .invalid-feedback');
        errorMessages.forEach(message => {
            message.setAttribute('role', 'alert');
            message.setAttribute('aria-live', 'polite');
        });
    }
    
    setupDashboardAriaLabels() {
        // Dashboard sections
        const dashboardSections = document.querySelectorAll('.dashboard-section, .bg-white.rounded-xl');
        dashboardSections.forEach((section, index) => {
            section.setAttribute('role', 'region');
            
            const heading = section.querySelector('h1, h2, h3, h4, h5, h6');
            if (heading) {
                const headingId = `section-heading-${index}`;
                heading.id = headingId;
                section.setAttribute('aria-labelledby', headingId);
            } else {
                section.setAttribute('aria-label', `Dashboard section ${index + 1}`);
            }
        });
        
        // Vehicle overview card
        const vehicleCard = document.querySelector('.vehicle-overview-card, [class*="vehicle"]');
        if (vehicleCard) {
            vehicleCard.setAttribute('role', 'region');
            vehicleCard.setAttribute('aria-label', 'Vehicle overview information');
        }
        
        // Promotions carousel
        const carousel = document.querySelector('[data-carousel], .carousel');
        if (carousel) {
            carousel.setAttribute('role', 'region');
            carousel.setAttribute('aria-label', 'Promotions and deals carousel');
            carousel.setAttribute('aria-live', 'polite');
        }
        
        // Quick tools grid
        const toolsGrid = document.querySelector('.quick-tools, .tools-grid');
        if (toolsGrid) {
            toolsGrid.setAttribute('role', 'region');
            toolsGrid.setAttribute('aria-label', 'Quick access tools');
        }
        
        // Service management section
        const serviceSection = document.querySelector('.service-management, .maintenance-section');
        if (serviceSection) {
            serviceSection.setAttribute('role', 'region');
            serviceSection.setAttribute('aria-label', 'Service management and maintenance information');
        }
    }
    
    setupSemanticStructure() {
        // Ensure proper heading hierarchy
        this.fixHeadingHierarchy();
        
        // Add semantic roles to layout elements
        this.addSemanticRoles();
        
        // Improve list structures
        this.improveListStructures();
        
        // Add landmark roles
        this.addLandmarkRoles();
    }
    
    fixHeadingHierarchy() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let currentLevel = 0;
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            
            // Ensure logical heading progression
            if (level > currentLevel + 1) {
                console.warn(`Heading level jump detected: ${heading.tagName} after h${currentLevel}`);
                // Could automatically fix by changing the heading level, but that might break styling
            }
            
            currentLevel = level;
        });
    }
    
    addSemanticRoles() {
        // Main content area
        const main = document.querySelector('main, .main-content, #main-content');
        if (main) {
            main.setAttribute('role', 'main');
        }
        
        // Header
        const header = document.querySelector('header, .header');
        if (header) {
            header.setAttribute('role', 'banner');
        }
        
        // Footer
        const footer = document.querySelector('footer, .footer');
        if (footer) {
            footer.setAttribute('role', 'contentinfo');
        }
        
        // Aside/sidebar
        const aside = document.querySelector('aside, .sidebar');
        if (aside) {
            aside.setAttribute('role', 'complementary');
        }
    }
    
    improveListStructures() {
        // Navigation lists
        const navLists = document.querySelectorAll('nav ul, .navigation ul');
        navLists.forEach(list => {
            list.setAttribute('role', 'menubar');
            
            const items = list.querySelectorAll('li');
            items.forEach(item => {
                item.setAttribute('role', 'menuitem');
            });
        });
        
        // Notification lists
        const notificationLists = document.querySelectorAll('.notifications ul, .alerts ul');
        notificationLists.forEach(list => {
            list.setAttribute('role', 'list');
            
            const items = list.querySelectorAll('li');
            items.forEach(item => {
                item.setAttribute('role', 'listitem');
            });
        });
    }
    
    addLandmarkRoles() {
        // Search functionality
        const search = document.querySelector('.search, [type="search"]');
        if (search) {
            const searchContainer = search.closest('form, div');
            if (searchContainer) {
                searchContainer.setAttribute('role', 'search');
            }
        }
        
        // Complementary content
        const complementary = document.querySelectorAll('.sidebar, .aside, .related');
        complementary.forEach(element => {
            element.setAttribute('role', 'complementary');
        });
    }
    
    setupKeyboardNavigation() {
        // Setup tab order
        this.setupTabOrder();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Setup focus trapping for modals
        this.setupFocusTrapping();
        
        // Setup arrow key navigation for menus
        this.setupArrowKeyNavigation();
    }
    
    setupTabOrder() {
        // Ensure logical tab order
        const focusableElements = this.getFocusableElements();
        
        focusableElements.forEach((element, index) => {
            // Remove any existing tabindex that might interfere
            if (element.getAttribute('tabindex') === '-1' && !element.hasAttribute('data-skip-focus')) {
                element.removeAttribute('tabindex');
            }
            
            // Ensure interactive elements are focusable
            if (element.tagName === 'DIV' && element.onclick) {
                element.setAttribute('tabindex', '0');
                element.setAttribute('role', 'button');
            }
        });
        
        // Hide decorative elements from tab order
        const decorativeElements = document.querySelectorAll('.decoration, .divider, .spacer');
        decorativeElements.forEach(element => {
            element.setAttribute('tabindex', '-1');
            element.setAttribute('aria-hidden', 'true');
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Skip if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Handle keyboard shortcuts
            if (e.altKey) {
                switch (e.key) {
                    case 'm':
                        e.preventDefault();
                        this.toggleMobileNav();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.focusNotifications();
                        break;
                    case 's':
                        e.preventDefault();
                        this.focusSearch();
                        break;
                    case 'h':
                        e.preventDefault();
                        this.focusHome();
                        break;
                }
            }
            
            // Handle escape key
            if (e.key === 'Escape') {
                this.handleEscapeKey();
            }
            
            // Handle enter and space for custom buttons
            if ((e.key === 'Enter' || e.key === ' ') && e.target.getAttribute('role') === 'button') {
                e.preventDefault();
                e.target.click();
            }
        });
    }
    
    setupFocusTrapping() {
        // Setup focus trapping for modals and dropdowns
        const modals = document.querySelectorAll('.modal, .dropdown, [role="dialog"]');
        
        modals.forEach(modal => {
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    this.trapFocus(e, modal);
                }
            });
        });
    }
    
    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }
    
    setupArrowKeyNavigation() {
        // Setup arrow key navigation for menus
        const menus = document.querySelectorAll('[role="menubar"], [role="menu"]');
        
        menus.forEach(menu => {
            menu.addEventListener('keydown', (e) => {
                const items = menu.querySelectorAll('[role="menuitem"]');
                const currentIndex = Array.from(items).indexOf(document.activeElement);
                
                switch (e.key) {
                    case 'ArrowDown':
                    case 'ArrowRight':
                        e.preventDefault();
                        const nextIndex = (currentIndex + 1) % items.length;
                        items[nextIndex].focus();
                        break;
                    case 'ArrowUp':
                    case 'ArrowLeft':
                        e.preventDefault();
                        const prevIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
                        items[prevIndex].focus();
                        break;
                    case 'Home':
                        e.preventDefault();
                        items[0].focus();
                        break;
                    case 'End':
                        e.preventDefault();
                        items[items.length - 1].focus();
                        break;
                }
            });
        });
    }
    
    setupScreenReaderSupport() {
        // Create screen reader announcements
        this.createScreenReaderAnnouncements();
        
        // Setup dynamic content announcements
        this.setupDynamicContentAnnouncements();
        
        // Setup status announcements
        this.setupStatusAnnouncements();
    }
    
    createScreenReaderAnnouncements() {
        // Create live regions for announcements
        const liveRegion = document.createElement('div');
        liveRegion.id = 'sr-live-region';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        document.body.appendChild(liveRegion);
        
        const assertiveRegion = document.createElement('div');
        assertiveRegion.id = 'sr-assertive-region';
        assertiveRegion.setAttribute('aria-live', 'assertive');
        assertiveRegion.setAttribute('aria-atomic', 'true');
        assertiveRegion.className = 'sr-only';
        document.body.appendChild(assertiveRegion);
        
        this.liveRegion = liveRegion;
        this.assertiveRegion = assertiveRegion;
    }
    
    setupDynamicContentAnnouncements() {
        // Announce when content changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    const addedElements = Array.from(mutation.addedNodes).filter(node => node.nodeType === 1);
                    
                    addedElements.forEach(element => {
                        if (element.classList.contains('notification') || element.classList.contains('alert')) {
                            const message = element.textContent.trim();
                            this.announceToScreenReader(message);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    setupStatusAnnouncements() {
        // Announce loading states
        window.announceLoadingState = (message) => {
            this.announceToScreenReader(message || 'Loading content');
        };
        
        // Announce success states
        window.announceSuccess = (message) => {
            this.announceToScreenReader(message || 'Action completed successfully');
        };
        
        // Announce error states
        window.announceError = (message) => {
            this.announceToScreenReader(message || 'An error occurred', true);
        };
    }
    
    setupFocusManagement() {
        // Setup focus indicators
        this.setupFocusIndicators();
        
        // Setup focus restoration
        this.setupFocusRestoration();
        
        // Setup skip links
        this.setupSkipLinks();
    }
    
    setupFocusIndicators() {
        // Enhanced focus indicators
        const style = document.createElement('style');
        style.textContent = `
            /* Enhanced focus indicators */
            *:focus-visible {
                outline: 2px solid #3b82f6 !important;
                outline-offset: 2px !important;
                border-radius: 4px;
            }
            
            /* High contrast focus indicators */
            @media (prefers-contrast: high) {
                *:focus-visible {
                    outline: 3px solid #000 !important;
                    outline-offset: 3px !important;
                }
            }
            
            /* Focus indicators for custom elements */
            [role="button"]:focus-visible,
            [tabindex]:focus-visible {
                outline: 2px solid #3b82f6 !important;
                outline-offset: 2px !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    setupFocusRestoration() {
        // Store focus before navigation
        let lastFocusedElement = null;
        
        document.addEventListener('focusout', (e) => {
            lastFocusedElement = e.target;
        });
        
        // Restore focus after page load
        window.addEventListener('load', () => {
            if (lastFocusedElement && lastFocusedElement.isConnected) {
                lastFocusedElement.focus();
            }
        });
    }
    
    setupSkipLinks() {
        // Create skip links
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
        `;
        
        document.body.insertBefore(skipLinks, document.body.firstChild);
        
        // Style skip links
        const skipLinkStyles = document.createElement('style');
        skipLinkStyles.textContent = `
            .skip-links {
                position: absolute;
                top: -100px;
                left: 0;
                z-index: 9999;
            }
            
            .skip-link {
                position: absolute;
                top: -100px;
                left: 0;
                background: #000;
                color: #fff;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 0 0 4px 0;
                font-weight: bold;
                transition: top 0.3s;
            }
            
            .skip-link:focus {
                top: 0;
            }
        `;
        document.head.appendChild(skipLinkStyles);
    }
    
    setupColorContrastCompliance() {
        // Check and fix color contrast issues
        this.checkColorContrast();
        
        // Setup high contrast mode support
        this.setupHighContrastMode();
        
        // Setup dark mode accessibility
        this.setupDarkModeAccessibility();
    }
    
    checkColorContrast() {
        // This would typically use a color contrast checking library
        // For now, we'll add CSS custom properties for better contrast control
        const contrastStyles = document.createElement('style');
        contrastStyles.textContent = `
            :root {
                --text-primary: #111827;
                --text-secondary: #4b5563;
                --text-muted: #6b7280;
                --bg-primary: #ffffff;
                --bg-secondary: #f9fafb;
                --border-color: #d1d5db;
                --focus-color: #3b82f6;
                --error-color: #dc2626;
                --success-color: #059669;
                --warning-color: #d97706;
            }
            
            /* Ensure minimum contrast ratios */
            .text-gray-500 {
                color: #6b7280 !important; /* 4.5:1 contrast ratio */
            }
            
            .text-gray-400 {
                color: #4b5563 !important; /* Better contrast */
            }
            
            /* High contrast mode overrides */
            @media (prefers-contrast: high) {
                :root {
                    --text-primary: #000000;
                    --text-secondary: #000000;
                    --text-muted: #333333;
                    --bg-primary: #ffffff;
                    --bg-secondary: #ffffff;
                    --border-color: #000000;
                }
                
                .text-gray-500,
                .text-gray-400,
                .text-gray-600 {
                    color: #000000 !important;
                }
                
                .bg-gray-50,
                .bg-gray-100 {
                    background-color: #ffffff !important;
                    border: 1px solid #000000 !important;
                }
            }
        `;
        document.head.appendChild(contrastStyles);
    }
    
    setupHighContrastMode() {
        // Detect high contrast preference
        const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
        
        const handleHighContrast = (e) => {
            if (e.matches) {
                document.body.classList.add('high-contrast');
                this.announceToScreenReader('High contrast mode enabled');
            } else {
                document.body.classList.remove('high-contrast');
            }
        };
        
        highContrastQuery.addListener(handleHighContrast);
        handleHighContrast(highContrastQuery);
    }
    
    setupDarkModeAccessibility() {
        // Ensure dark mode maintains accessibility
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleDarkMode = (e) => {
            if (e.matches) {
                document.body.classList.add('dark-mode-accessible');
            } else {
                document.body.classList.remove('dark-mode-accessible');
            }
        };
        
        darkModeQuery.addListener(handleDarkMode);
        handleDarkMode(darkModeQuery);
    }
    
    setupAccessibilityShortcuts() {
        // Create accessibility shortcuts panel
        const shortcutsPanel = document.createElement('div');
        shortcutsPanel.id = 'accessibility-shortcuts';
        shortcutsPanel.className = 'sr-only';
        shortcutsPanel.innerHTML = `
            <h2>Keyboard Shortcuts</h2>
            <ul>
                <li>Alt + M: Toggle mobile navigation</li>
                <li>Alt + N: Focus notifications</li>
                <li>Alt + S: Focus search</li>
                <li>Alt + H: Go to home</li>
                <li>Escape: Close modals and dropdowns</li>
                <li>Tab: Navigate forward</li>
                <li>Shift + Tab: Navigate backward</li>
                <li>Arrow keys: Navigate menus</li>
            </ul>
        `;
        document.body.appendChild(shortcutsPanel);
    }
    
    setupLiveRegions() {
        // Setup live regions for dynamic content
        const statusRegion = document.createElement('div');
        statusRegion.id = 'status-region';
        statusRegion.setAttribute('aria-live', 'polite');
        statusRegion.setAttribute('aria-label', 'Status updates');
        statusRegion.className = 'sr-only';
        document.body.appendChild(statusRegion);
        
        this.statusRegion = statusRegion;
    }
    
    // Utility Methods
    getFocusableElements() {
        return document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"]'
        );
    }
    
    announceToScreenReader(message, assertive = false) {
        const region = assertive ? this.assertiveRegion : this.liveRegion;
        
        if (region) {
            region.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }
    
    toggleMobileNav() {
        const mobileNavToggle = document.getElementById('mobile-nav-toggle');
        if (mobileNavToggle) {
            mobileNavToggle.click();
            this.announceToScreenReader('Mobile navigation toggled');
        }
    }
    
    focusNotifications() {
        const notificationsButton = document.getElementById('notifications-button');
        if (notificationsButton) {
            notificationsButton.focus();
            this.announceToScreenReader('Focused on notifications');
        }
    }
    
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], .search input');
        if (searchInput) {
            searchInput.focus();
            this.announceToScreenReader('Focused on search');
        }
    }
    
    focusHome() {
        const homeLink = document.querySelector('a[href="/"], .logo a, .brand a');
        if (homeLink) {
            homeLink.focus();
            this.announceToScreenReader('Focused on home link');
        }
    }
    
    handleEscapeKey() {
        // Close any open modals or dropdowns
        const openModals = document.querySelectorAll('.modal.show, .dropdown.show, [aria-expanded="true"]');
        
        openModals.forEach(modal => {
            if (modal.classList.contains('modal')) {
                modal.classList.remove('show');
            } else if (modal.classList.contains('dropdown')) {
                modal.classList.remove('show');
            } else {
                modal.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close mobile navigation
        const mobileNav = document.getElementById('mobile-nav');
        if (mobileNav && !mobileNav.classList.contains('-translate-x-full')) {
            const closeButton = document.getElementById('mobile-nav-close');
            if (closeButton) {
                closeButton.click();
            }
        }
    }
    
    // Public API
    updateAriaLabel(element, label) {
        element.setAttribute('aria-label', label);
    }
    
    announceStatus(message) {
        if (this.statusRegion) {
            this.statusRegion.textContent = message;
            setTimeout(() => {
                this.statusRegion.textContent = '';
            }, 3000);
        }
    }
    
    setFocusToElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.focus();
            return true;
        }
        return false;
    }
    
    // Cleanup method
    destroy() {
        // Remove created elements
        const elementsToRemove = [
            '#sr-live-region',
            '#sr-assertive-region',
            '#status-region',
            '#accessibility-shortcuts',
            '.skip-links'
        ];
        
        elementsToRemove.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.remove();
            }
        });
        
        this.isInitialized = false;
    }
}

// Screen reader only utility class
const srOnlyCSS = `
.sr-only {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}

.sr-only-focusable:focus {
    position: static !important;
    width: auto !important;
    height: auto !important;
    padding: inherit !important;
    margin: inherit !important;
    overflow: visible !important;
    clip: auto !important;
    white-space: normal !important;
}
`;

// Inject screen reader CSS
const srStyleSheet = document.createElement('style');
srStyleSheet.textContent = srOnlyCSS;
document.head.appendChild(srStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.accessibilityEnhancements = new AccessibilityEnhancements();
});

// Export for external use
window.AccessibilityEnhancements = AccessibilityEnhancements;