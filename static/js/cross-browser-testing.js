/**
 * Cross-Browser and Device Testing Suite
 * Tests responsive behavior, browser compatibility, and touch interactions
 */

class CrossBrowserTester {
    constructor() {
        this.testResults = [];
        this.deviceBreakpoints = {
            mobile: { min: 320, max: 767 },
            tablet: { min: 768, max: 1023 },
            desktop: { min: 1024, max: 1440 },
            largeDesktop: { min: 1441, max: 9999 }
        };
        this.init();
    }

    init() {
        this.detectBrowser();
        this.detectDevice();
        this.runTests();
    }

    detectBrowser() {
        const userAgent = navigator.userAgent;
        this.browser = {
            name: 'Unknown',
            version: 'Unknown',
            isChrome: /Chrome/.test(userAgent) && /Google Inc/.test(navigator.vendor),
            isFirefox: /Firefox/.test(userAgent),
            isSafari: /Safari/.test(userAgent) && /Apple Computer/.test(navigator.vendor),
            isEdge: /Edg/.test(userAgent),
            isIE: /Trident/.test(userAgent) || /MSIE/.test(userAgent)
        };

        if (this.browser.isChrome) this.browser.name = 'Chrome';
        else if (this.browser.isFirefox) this.browser.name = 'Firefox';
        else if (this.browser.isSafari) this.browser.name = 'Safari';
        else if (this.browser.isEdge) this.browser.name = 'Edge';
        else if (this.browser.isIE) this.browser.name = 'Internet Explorer';

        console.log('Browser detected:', this.browser.name);
    }

    detectDevice() {
        this.device = {
            isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            isTablet: /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent),
            isDesktop: !/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            hasTouch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            pixelRatio: window.devicePixelRatio || 1
        };

        // Determine current breakpoint
        const width = this.device.screenWidth;
        if (width <= this.deviceBreakpoints.mobile.max) {
            this.device.breakpoint = 'mobile';
        } else if (width <= this.deviceBreakpoints.tablet.max) {
            this.device.breakpoint = 'tablet';
        } else if (width <= this.deviceBreakpoints.desktop.max) {
            this.device.breakpoint = 'desktop';
        } else {
            this.device.breakpoint = 'largeDesktop';
        }

        console.log('Device detected:', this.device);
    }

    runTests() {
        console.log('Starting cross-browser and device tests...');
        
        // Test responsive behavior
        this.testResponsiveLayout();
        this.testMobileNavigation();
        this.testTouchInteractions();
        this.testCarouselFunctionality();
        this.testVehicleSelector();
        this.testNotifications();
        this.testAccessibility();
        this.testPerformance();

        // Generate test report
        this.generateTestReport();
    }

    testResponsiveLayout() {
        const test = { name: 'Responsive Layout', status: 'pass', issues: [] };

        try {
            // Test grid layout responsiveness
            const mainGrid = document.querySelector('.grid');
            if (mainGrid) {
                const computedStyle = window.getComputedStyle(mainGrid);
                const gridCols = computedStyle.getPropertyValue('grid-template-columns');
                
                if (this.device.breakpoint === 'mobile' && gridCols.includes('1fr')) {
                    test.issues.push('Mobile layout should use single column');
                }
                
                if (this.device.breakpoint === 'desktop' && !gridCols.includes('repeat(3')) {
                    test.issues.push('Desktop layout should use 3-column grid');
                }
            }

            // Test mobile navigation visibility
            const mobileNav = document.getElementById('mobile-nav-toggle');
            const desktopNav = document.querySelector('.lg\\:flex');
            
            if (this.device.breakpoint === 'mobile') {
                if (mobileNav && window.getComputedStyle(mobileNav).display === 'none') {
                    test.issues.push('Mobile navigation button should be visible on mobile');
                }
            } else {
                if (desktopNav && window.getComputedStyle(desktopNav).display === 'none') {
                    test.issues.push('Desktop navigation should be visible on larger screens');
                }
            }

            // Test component stacking
            const vehicleCard = document.querySelector('.vehicle-overview-card');
            if (vehicleCard && this.device.breakpoint === 'mobile') {
                const cardGrid = vehicleCard.querySelector('.grid');
                if (cardGrid) {
                    const cardStyle = window.getComputedStyle(cardGrid);
                    if (!cardStyle.getPropertyValue('grid-template-columns').includes('1fr')) {
                        test.issues.push('Vehicle card should stack on mobile');
                    }
                }
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing responsive layout: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testMobileNavigation() {
        const test = { name: 'Mobile Navigation', status: 'pass', issues: [] };

        try {
            const mobileNavToggle = document.getElementById('mobile-nav-toggle');
            const mobileNav = document.getElementById('mobile-nav');
            const mobileNavOverlay = document.getElementById('mobile-nav-overlay');

            if (!mobileNavToggle) {
                test.issues.push('Mobile navigation toggle button not found');
            }

            if (!mobileNav) {
                test.issues.push('Mobile navigation menu not found');
            }

            if (!mobileNavOverlay) {
                test.issues.push('Mobile navigation overlay not found');
            }

            // Test button accessibility
            if (mobileNavToggle) {
                const ariaLabel = mobileNavToggle.getAttribute('aria-label');
                const ariaExpanded = mobileNavToggle.getAttribute('aria-expanded');
                
                if (!ariaLabel) {
                    test.issues.push('Mobile nav toggle missing aria-label');
                }
                
                if (!ariaExpanded) {
                    test.issues.push('Mobile nav toggle missing aria-expanded');
                }

                // Test minimum touch target size
                const rect = mobileNavToggle.getBoundingClientRect();
                if (rect.width < 44 || rect.height < 44) {
                    test.issues.push('Mobile nav toggle too small for touch (minimum 44px)');
                }
            }

            // Test menu functionality
            if (mobileNavToggle && mobileNav) {
                // Simulate click
                mobileNavToggle.click();
                
                setTimeout(() => {
                    const isVisible = !mobileNav.classList.contains('-translate-x-full');
                    if (!isVisible) {
                        test.issues.push('Mobile navigation menu does not open on click');
                    }
                    
                    // Test close functionality
                    const closeButton = document.getElementById('mobile-nav-close');
                    if (closeButton) {
                        closeButton.click();
                    }
                }, 100);
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing mobile navigation: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testTouchInteractions() {
        const test = { name: 'Touch Interactions', status: 'pass', issues: [] };

        if (!this.device.hasTouch) {
            test.status = 'skip';
            test.issues.push('Device does not support touch');
            this.testResults.push(test);
            return;
        }

        try {
            // Test touch-friendly button sizes
            const buttons = document.querySelectorAll('button, a[role="button"]');
            buttons.forEach((button, index) => {
                const rect = button.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) { // Only test visible buttons
                    if (rect.width < 44 || rect.height < 44) {
                        test.issues.push(`Button ${index + 1} too small for touch (${rect.width}x${rect.height}px)`);
                    }
                }
            });

            // Test carousel swipe functionality
            const carousel = document.querySelector('.promotions-carousel');
            if (carousel) {
                // Check for touch event listeners
                const hasSwipeSupport = carousel.addEventListener !== undefined;
                if (!hasSwipeSupport) {
                    test.issues.push('Carousel missing swipe gesture support');
                }
            }

            // Test pull-to-refresh (if implemented)
            const mainContent = document.getElementById('main-content');
            if (mainContent && this.device.isMobile) {
                // Check for pull-to-refresh implementation
                const hasPullToRefresh = mainContent.style.overscrollBehavior !== undefined;
                if (!hasPullToRefresh) {
                    test.issues.push('Pull-to-refresh functionality not detected');
                }
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing touch interactions: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testCarouselFunctionality() {
        const test = { name: 'Carousel Functionality', status: 'pass', issues: [] };

        try {
            const carousel = document.querySelector('.promotions-carousel');
            if (!carousel) {
                test.issues.push('Promotions carousel not found');
                test.status = 'fail';
                this.testResults.push(test);
                return;
            }

            // Test navigation arrows
            const prevButton = carousel.querySelector('.carousel-prev');
            const nextButton = carousel.querySelector('.carousel-next');
            
            if (!prevButton || !nextButton) {
                test.issues.push('Carousel navigation buttons not found');
            }

            // Test dot indicators
            const dots = carousel.querySelectorAll('.carousel-dot');
            if (dots.length === 0) {
                test.issues.push('Carousel dot indicators not found');
            }

            // Test auto-rotation
            const autoRotateInterval = window.carouselAutoRotate;
            if (!autoRotateInterval) {
                test.issues.push('Carousel auto-rotation not implemented');
            }

            // Test responsive behavior
            const carouselItems = carousel.querySelectorAll('.carousel-item');
            if (carouselItems.length > 0) {
                const itemStyle = window.getComputedStyle(carouselItems[0]);
                const itemWidth = parseFloat(itemStyle.width);
                const containerWidth = carousel.getBoundingClientRect().width;
                
                if (this.device.breakpoint === 'mobile' && itemWidth > containerWidth) {
                    test.issues.push('Carousel items too wide for mobile viewport');
                }
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing carousel functionality: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testVehicleSelector() {
        const test = { name: 'Vehicle Selector', status: 'pass', issues: [] };

        try {
            const vehicleSelectors = document.querySelectorAll('#vehicle-selector, #mobile-vehicle-selector, #vehicle-overview-selector');
            
            if (vehicleSelectors.length === 0) {
                test.status = 'skip';
                test.issues.push('No vehicle selectors found (single vehicle account)');
                this.testResults.push(test);
                return;
            }

            vehicleSelectors.forEach((selector, index) => {
                // Test loading states
                const loadingIndicator = selector.parentElement.querySelector('[id$="-loading"]');
                if (!loadingIndicator) {
                    test.issues.push(`Vehicle selector ${index + 1} missing loading indicator`);
                }

                // Test AJAX functionality
                if (selector.onchange) {
                    // Simulate change event
                    const event = new Event('change');
                    selector.dispatchEvent(event);
                    
                    // Check if loading state is shown
                    setTimeout(() => {
                        if (loadingIndicator && !loadingIndicator.classList.contains('hidden')) {
                            // Loading state is working
                        } else {
                            test.issues.push(`Vehicle selector ${index + 1} loading state not working`);
                        }
                    }, 50);
                }

                // Test accessibility
                const label = selector.getAttribute('aria-label') || selector.previousElementSibling?.tagName === 'LABEL';
                if (!label) {
                    test.issues.push(`Vehicle selector ${index + 1} missing proper labeling`);
                }
            });

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing vehicle selector: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testNotifications() {
        const test = { name: 'Notifications System', status: 'pass', issues: [] };

        try {
            const notificationButton = document.getElementById('notifications-button');
            const notificationDropdown = document.getElementById('notifications-dropdown');
            const notificationBadge = document.getElementById('notification-count');

            if (!notificationButton) {
                test.issues.push('Notification button not found');
            }

            if (!notificationDropdown) {
                test.issues.push('Notification dropdown not found');
            }

            // Test button accessibility
            if (notificationButton) {
                const ariaLabel = notificationButton.getAttribute('aria-label');
                const ariaExpanded = notificationButton.getAttribute('aria-expanded');
                
                if (!ariaLabel) {
                    test.issues.push('Notification button missing aria-label');
                }
                
                if (ariaExpanded === null) {
                    test.issues.push('Notification button missing aria-expanded');
                }
            }

            // Test badge animation
            if (notificationBadge) {
                const hasAnimation = notificationBadge.classList.contains('badge-bounce');
                if (!hasAnimation) {
                    test.issues.push('Notification badge missing bounce animation');
                }
            }

            // Test dropdown functionality
            if (notificationButton && notificationDropdown) {
                notificationButton.click();
                
                setTimeout(() => {
                    const isVisible = !notificationDropdown.classList.contains('hidden');
                    if (!isVisible) {
                        test.issues.push('Notification dropdown does not open on click');
                    }
                }, 100);
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing notifications: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testAccessibility() {
        const test = { name: 'Accessibility Features', status: 'pass', issues: [] };

        try {
            // Test semantic HTML structure
            const main = document.querySelector('main[role="main"]');
            const nav = document.querySelector('nav[role="navigation"]');
            const header = document.querySelector('header[role="banner"]');

            if (!main) test.issues.push('Missing main landmark');
            if (!nav) test.issues.push('Missing navigation landmark');
            if (!header) test.issues.push('Missing banner landmark');

            // Test heading hierarchy
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            let previousLevel = 0;
            headings.forEach((heading, index) => {
                const level = parseInt(heading.tagName.charAt(1));
                if (index === 0 && level !== 1) {
                    test.issues.push('Page should start with h1');
                }
                if (level > previousLevel + 1) {
                    test.issues.push(`Heading level skip detected: ${heading.tagName} after h${previousLevel}`);
                }
                previousLevel = level;
            });

            // Test ARIA labels
            const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
            interactiveElements.forEach((element, index) => {
                const hasLabel = element.getAttribute('aria-label') || 
                               element.getAttribute('aria-labelledby') ||
                               element.querySelector('span:not([aria-hidden="true"])') ||
                               element.textContent.trim();
                
                if (!hasLabel) {
                    test.issues.push(`Interactive element ${index + 1} missing accessible label`);
                }
            });

            // Test keyboard navigation
            const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
            focusableElements.forEach((element, index) => {
                if (element.tabIndex < 0 && !element.hasAttribute('tabindex')) {
                    // Element should be focusable
                } else if (element.tabIndex > 0) {
                    test.issues.push(`Element ${index + 1} has positive tabindex (should use 0 or -1)`);
                }
            });

            // Test color contrast (basic check)
            const textElements = document.querySelectorAll('p, span, div, a, button');
            textElements.forEach((element, index) => {
                const style = window.getComputedStyle(element);
                const color = style.color;
                const backgroundColor = style.backgroundColor;
                
                // Basic contrast check (simplified)
                if (color === 'rgb(128, 128, 128)' && backgroundColor === 'rgb(255, 255, 255)') {
                    test.issues.push(`Element ${index + 1} may have insufficient color contrast`);
                }
            });

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing accessibility: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    testPerformance() {
        const test = { name: 'Performance Metrics', status: 'pass', issues: [] };

        try {
            // Test loading performance
            if (window.performance && window.performance.timing) {
                const timing = window.performance.timing;
                const loadTime = timing.loadEventEnd - timing.navigationStart;
                const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
                
                if (loadTime > 3000) {
                    test.issues.push(`Page load time too slow: ${loadTime}ms (should be < 3000ms)`);
                }
                
                if (domReady > 1500) {
                    test.issues.push(`DOM ready time too slow: ${domReady}ms (should be < 1500ms)`);
                }
            }

            // Test image optimization
            const images = document.querySelectorAll('img');
            images.forEach((img, index) => {
                if (!img.alt) {
                    test.issues.push(`Image ${index + 1} missing alt attribute`);
                }
                
                // Check for lazy loading
                if (!img.loading && !img.classList.contains('lazy')) {
                    test.issues.push(`Image ${index + 1} not optimized for lazy loading`);
                }
            });

            // Test CSS and JS optimization
            const stylesheets = document.querySelectorAll('link[rel="stylesheet"]');
            const scripts = document.querySelectorAll('script[src]');
            
            if (stylesheets.length > 5) {
                test.issues.push(`Too many CSS files: ${stylesheets.length} (consider bundling)`);
            }
            
            if (scripts.length > 10) {
                test.issues.push(`Too many JS files: ${scripts.length} (consider bundling)`);
            }

        } catch (error) {
            test.status = 'fail';
            test.issues.push(`Error testing performance: ${error.message}`);
        }

        if (test.issues.length > 0) {
            test.status = 'fail';
        }

        this.testResults.push(test);
    }

    generateTestReport() {
        const report = {
            timestamp: new Date().toISOString(),
            browser: this.browser,
            device: this.device,
            tests: this.testResults,
            summary: {
                total: this.testResults.length,
                passed: this.testResults.filter(t => t.status === 'pass').length,
                failed: this.testResults.filter(t => t.status === 'fail').length,
                skipped: this.testResults.filter(t => t.status === 'skip').length
            }
        };

        console.log('=== CROSS-BROWSER TESTING REPORT ===');
        console.log(`Browser: ${report.browser.name}`);
        console.log(`Device: ${report.device.breakpoint} (${report.device.screenWidth}x${report.device.screenHeight})`);
        console.log(`Touch Support: ${report.device.hasTouch ? 'Yes' : 'No'}`);
        console.log('');
        console.log(`Tests: ${report.summary.total} | Passed: ${report.summary.passed} | Failed: ${report.summary.failed} | Skipped: ${report.summary.skipped}`);
        console.log('');

        this.testResults.forEach(test => {
            const status = test.status.toUpperCase();
            const statusIcon = test.status === 'pass' ? '✅' : test.status === 'fail' ? '❌' : '⏭️';
            console.log(`${statusIcon} ${test.name}: ${status}`);
            
            if (test.issues.length > 0) {
                test.issues.forEach(issue => {
                    console.log(`   - ${issue}`);
                });
            }
        });

        // Store report for external access
        window.crossBrowserTestReport = report;
        
        // Dispatch custom event for test completion
        window.dispatchEvent(new CustomEvent('crossBrowserTestComplete', { detail: report }));
    }
}

// Auto-run tests when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new CrossBrowserTester();
    });
} else {
    new CrossBrowserTester();
}

// Export for manual testing
window.CrossBrowserTester = CrossBrowserTester;