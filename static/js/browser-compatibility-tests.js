/**
 * Browser Compatibility Testing Suite
 * Tests functionality across different browsers and versions
 */

class BrowserCompatibilityTester {
    constructor() {
        this.browserFeatures = {
            // CSS Features
            'CSS Grid': () => CSS.supports('display', 'grid'),
            'CSS Flexbox': () => CSS.supports('display', 'flex'),
            'CSS Custom Properties': () => CSS.supports('--test', 'value'),
            'CSS Transforms': () => CSS.supports('transform', 'translateX(0)'),
            'CSS Transitions': () => CSS.supports('transition', 'all 0.3s'),
            'CSS Animations': () => CSS.supports('animation', 'test 1s'),
            
            // JavaScript Features
            'ES6 Arrow Functions': () => {
                try {
                    eval('() => {}');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            'ES6 Template Literals': () => {
                try {
                    eval('`test`');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            'ES6 Destructuring': () => {
                try {
                    eval('const {a} = {a: 1}');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            'Fetch API': () => typeof fetch !== 'undefined',
            'Promise': () => typeof Promise !== 'undefined',
            'Async/Await': () => {
                try {
                    eval('async function test() { await Promise.resolve(); }');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            
            // DOM Features
            'querySelector': () => typeof document.querySelector !== 'undefined',
            'addEventListener': () => typeof document.addEventListener !== 'undefined',
            'classList': () => typeof document.createElement('div').classList !== 'undefined',
            'dataset': () => typeof document.createElement('div').dataset !== 'undefined',
            
            // Touch and Mobile Features
            'Touch Events': () => 'ontouchstart' in window,
            'Pointer Events': () => 'onpointerdown' in window,
            'Device Orientation': () => 'ondeviceorientation' in window,
            'Geolocation': () => 'geolocation' in navigator,
            
            // Storage Features
            'localStorage': () => {
                try {
                    localStorage.setItem('test', 'test');
                    localStorage.removeItem('test');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            'sessionStorage': () => {
                try {
                    sessionStorage.setItem('test', 'test');
                    sessionStorage.removeItem('test');
                    return true;
                } catch (e) {
                    return false;
                }
            },
            
            // Media Features
            'WebP Support': () => {
                const canvas = document.createElement('canvas');
                canvas.width = 1;
                canvas.height = 1;
                return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
            },
            'Video Element': () => typeof document.createElement('video').play !== 'undefined',
            'Audio Element': () => typeof document.createElement('audio').play !== 'undefined'
        };
        
        this.browserInfo = this.detectBrowser();
        this.testResults = [];
        this.init();
    }

    init() {
        this.runCompatibilityTests();
        this.testDashboardFeatures();
        this.generateCompatibilityReport();
    }

    detectBrowser() {
        const userAgent = navigator.userAgent;
        const vendor = navigator.vendor;
        
        let browser = {
            name: 'Unknown',
            version: 'Unknown',
            engine: 'Unknown',
            isSupported: true,
            warnings: []
        };

        // Chrome
        if (/Chrome/.test(userAgent) && /Google Inc/.test(vendor)) {
            browser.name = 'Chrome';
            const match = userAgent.match(/Chrome\/(\d+)/);
            browser.version = match ? match[1] : 'Unknown';
            browser.engine = 'Blink';
            if (parseInt(browser.version) < 70) {
                browser.isSupported = false;
                browser.warnings.push('Chrome version too old (minimum: 70)');
            }
        }
        // Firefox
        else if (/Firefox/.test(userAgent)) {
            browser.name = 'Firefox';
            const match = userAgent.match(/Firefox\/(\d+)/);
            browser.version = match ? match[1] : 'Unknown';
            browser.engine = 'Gecko';
            if (parseInt(browser.version) < 65) {
                browser.isSupported = false;
                browser.warnings.push('Firefox version too old (minimum: 65)');
            }
        }
        // Safari
        else if (/Safari/.test(userAgent) && /Apple Computer/.test(vendor)) {
            browser.name = 'Safari';
            const match = userAgent.match(/Version\/(\d+)/);
            browser.version = match ? match[1] : 'Unknown';
            browser.engine = 'WebKit';
            if (parseInt(browser.version) < 12) {
                browser.isSupported = false;
                browser.warnings.push('Safari version too old (minimum: 12)');
            }
        }
        // Edge
        else if (/Edg/.test(userAgent)) {
            browser.name = 'Edge';
            const match = userAgent.match(/Edg\/(\d+)/);
            browser.version = match ? match[1] : 'Unknown';
            browser.engine = 'Blink';
            if (parseInt(browser.version) < 79) {
                browser.isSupported = false;
                browser.warnings.push('Edge version too old (minimum: 79)');
            }
        }
        // Internet Explorer
        else if (/Trident/.test(userAgent) || /MSIE/.test(userAgent)) {
            browser.name = 'Internet Explorer';
            const match = userAgent.match(/(?:MSIE |rv:)(\d+)/);
            browser.version = match ? match[1] : 'Unknown';
            browser.engine = 'Trident';
            browser.isSupported = false;
            browser.warnings.push('Internet Explorer is not supported');
        }

        return browser;
    }

    runCompatibilityTests() {
        console.log('Running browser compatibility tests...');
        
        Object.entries(this.browserFeatures).forEach(([feature, test]) => {
            try {
                const isSupported = test();
                this.testResults.push({
                    feature,
                    supported: isSupported,
                    critical: this.isCriticalFeature(feature)
                });
            } catch (error) {
                this.testResults.push({
                    feature,
                    supported: false,
                    critical: this.isCriticalFeature(feature),
                    error: error.message
                });
            }
        });
    }

    isCriticalFeature(feature) {
        const criticalFeatures = [
            'CSS Flexbox',
            'querySelector',
            'addEventListener',
            'classList',
            'Fetch API',
            'Promise',
            'localStorage'
        ];
        return criticalFeatures.includes(feature);
    }

    testDashboardFeatures() {
        console.log('Testing dashboard-specific functionality...');
        
        const dashboardTests = [
            {
                name: 'Mobile Navigation Toggle',
                test: () => {
                    const toggle = document.getElementById('mobile-nav-toggle');
                    const nav = document.getElementById('mobile-nav');
                    return toggle && nav && typeof toggle.click === 'function';
                },
                critical: true
            },
            {
                name: 'Vehicle Selector Functionality',
                test: () => {
                    const selector = document.getElementById('vehicle-selector');
                    return selector && typeof selector.addEventListener === 'function';
                },
                critical: false
            },
            {
                name: 'Notification Dropdown',
                test: () => {
                    const button = document.getElementById('notifications-button');
                    const dropdown = document.getElementById('notifications-dropdown');
                    return button && dropdown;
                },
                critical: false
            },
            {
                name: 'Carousel Navigation',
                test: () => {
                    const carousel = document.querySelector('.promotions-carousel');
                    if (!carousel) return true; // Skip if not present
                    const prevBtn = carousel.querySelector('.carousel-prev');
                    const nextBtn = carousel.querySelector('.carousel-next');
                    return prevBtn && nextBtn;
                },
                critical: false
            },
            {
                name: 'Touch Event Support',
                test: () => {
                    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
                },
                critical: false
            },
            {
                name: 'CSS Grid Layout',
                test: () => {
                    const grid = document.querySelector('.grid');
                    if (!grid) return false;
                    const style = window.getComputedStyle(grid);
                    return style.display === 'grid';
                },
                critical: true
            },
            {
                name: 'Responsive Images',
                test: () => {
                    const images = document.querySelectorAll('img');
                    return Array.from(images).every(img => 
                        img.style.maxWidth === '100%' || 
                        window.getComputedStyle(img).maxWidth === '100%'
                    );
                },
                critical: false
            },
            {
                name: 'ARIA Accessibility',
                test: () => {
                    const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby], [role]');
                    return ariaElements.length > 0;
                },
                critical: true
            }
        ];

        dashboardTests.forEach(({ name, test, critical }) => {
            try {
                const result = test();
                this.testResults.push({
                    feature: name,
                    supported: result,
                    critical: critical,
                    category: 'Dashboard'
                });
            } catch (error) {
                this.testResults.push({
                    feature: name,
                    supported: false,
                    critical: critical,
                    category: 'Dashboard',
                    error: error.message
                });
            }
        });
    }

    generateCompatibilityReport() {
        const criticalFailures = this.testResults.filter(t => !t.supported && t.critical);
        const warnings = this.testResults.filter(t => !t.supported && !t.critical);
        const passed = this.testResults.filter(t => t.supported);

        const report = {
            browser: this.browserInfo,
            timestamp: new Date().toISOString(),
            summary: {
                total: this.testResults.length,
                passed: passed.length,
                criticalFailures: criticalFailures.length,
                warnings: warnings.length,
                isCompatible: criticalFailures.length === 0 && this.browserInfo.isSupported
            },
            results: this.testResults,
            recommendations: this.generateRecommendations(criticalFailures, warnings)
        };

        this.displayReport(report);
        window.browserCompatibilityReport = report;
        
        // Dispatch event for external listeners
        window.dispatchEvent(new CustomEvent('browserCompatibilityTestComplete', { detail: report }));
    }

    generateRecommendations(criticalFailures, warnings) {
        const recommendations = [];

        if (!this.browserInfo.isSupported) {
            recommendations.push({
                type: 'critical',
                message: `Please upgrade to a supported browser version. Current: ${this.browserInfo.name} ${this.browserInfo.version}`,
                action: 'Upgrade browser'
            });
        }

        if (criticalFailures.length > 0) {
            recommendations.push({
                type: 'critical',
                message: `${criticalFailures.length} critical features are not supported. The dashboard may not function properly.`,
                action: 'Consider using a modern browser'
            });
        }

        if (warnings.length > 0) {
            recommendations.push({
                type: 'warning',
                message: `${warnings.length} optional features are not supported. Some functionality may be limited.`,
                action: 'Update browser for best experience'
            });
        }

        // Specific feature recommendations
        const unsupportedFeatures = this.testResults.filter(t => !t.supported);
        
        if (unsupportedFeatures.some(f => f.feature === 'Touch Events')) {
            recommendations.push({
                type: 'info',
                message: 'Touch events not supported. Mobile interactions may be limited.',
                action: 'Use mouse/trackpad for navigation'
            });
        }

        if (unsupportedFeatures.some(f => f.feature === 'WebP Support')) {
            recommendations.push({
                type: 'info',
                message: 'WebP images not supported. Fallback images will be used.',
                action: 'No action required'
            });
        }

        return recommendations;
    }

    displayReport(report) {
        console.log('=== BROWSER COMPATIBILITY REPORT ===');
        console.log(`Browser: ${report.browser.name} ${report.browser.version} (${report.browser.engine})`);
        console.log(`Compatible: ${report.summary.isCompatible ? 'Yes' : 'No'}`);
        console.log(`Tests: ${report.summary.total} | Passed: ${report.summary.passed} | Critical Failures: ${report.summary.criticalFailures} | Warnings: ${report.summary.warnings}`);
        console.log('');

        if (report.browser.warnings.length > 0) {
            console.log('Browser Warnings:');
            report.browser.warnings.forEach(warning => {
                console.log(`⚠️  ${warning}`);
            });
            console.log('');
        }

        if (report.summary.criticalFailures > 0) {
            console.log('Critical Failures:');
            this.testResults.filter(t => !t.supported && t.critical).forEach(test => {
                console.log(`❌ ${test.feature}${test.error ? ` (${test.error})` : ''}`);
            });
            console.log('');
        }

        if (report.summary.warnings > 0) {
            console.log('Warnings:');
            this.testResults.filter(t => !t.supported && !t.critical).forEach(test => {
                console.log(`⚠️  ${test.feature}${test.error ? ` (${test.error})` : ''}`);
            });
            console.log('');
        }

        if (report.recommendations.length > 0) {
            console.log('Recommendations:');
            report.recommendations.forEach(rec => {
                const icon = rec.type === 'critical' ? '🚨' : rec.type === 'warning' ? '⚠️' : 'ℹ️';
                console.log(`${icon} ${rec.message}`);
                console.log(`   Action: ${rec.action}`);
            });
        }

        // Show success message if all tests pass
        if (report.summary.isCompatible && report.summary.criticalFailures === 0) {
            console.log('✅ All compatibility tests passed! Dashboard should work perfectly in this browser.');
        }
    }

    // Method to test specific browser quirks
    testBrowserQuirks() {
        const quirks = [];

        // Safari-specific issues
        if (this.browserInfo.name === 'Safari') {
            // Test for Safari's flexbox bugs
            const testDiv = document.createElement('div');
            testDiv.style.display = 'flex';
            testDiv.style.flexDirection = 'column';
            document.body.appendChild(testDiv);
            
            const computedStyle = window.getComputedStyle(testDiv);
            if (computedStyle.flexDirection !== 'column') {
                quirks.push('Safari flexbox column direction bug detected');
            }
            
            document.body.removeChild(testDiv);
        }

        // Firefox-specific issues
        if (this.browserInfo.name === 'Firefox') {
            // Test for Firefox's CSS Grid bugs
            if (!CSS.supports('grid-template-columns', 'subgrid')) {
                quirks.push('Firefox subgrid not supported');
            }
        }

        // Edge-specific issues
        if (this.browserInfo.name === 'Edge' && parseInt(this.browserInfo.version) < 79) {
            quirks.push('Legacy Edge detected - may have CSS Grid issues');
        }

        return quirks;
    }
}

// Auto-run compatibility tests
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new BrowserCompatibilityTester();
    });
} else {
    new BrowserCompatibilityTester();
}

// Export for manual testing
window.BrowserCompatibilityTester = BrowserCompatibilityTester;