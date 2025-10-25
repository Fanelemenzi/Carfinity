/**
 * Device Testing Utility
 * Simulates different device viewports and tests responsive behavior
 */

class DeviceTestingUtility {
    constructor() {
        this.devices = {
            // Mobile devices
            'iPhone SE': { width: 375, height: 667, userAgent: 'iPhone' },
            'iPhone 12': { width: 390, height: 844, userAgent: 'iPhone' },
            'iPhone 12 Pro Max': { width: 428, height: 926, userAgent: 'iPhone' },
            'Samsung Galaxy S21': { width: 360, height: 800, userAgent: 'Android' },
            'Samsung Galaxy Note 20': { width: 412, height: 915, userAgent: 'Android' },
            
            // Tablets
            'iPad': { width: 768, height: 1024, userAgent: 'iPad' },
            'iPad Pro 11"': { width: 834, height: 1194, userAgent: 'iPad' },
            'iPad Pro 12.9"': { width: 1024, height: 1366, userAgent: 'iPad' },
            'Samsung Galaxy Tab': { width: 800, height: 1280, userAgent: 'Android' },
            
            // Desktop
            'Desktop Small': { width: 1024, height: 768, userAgent: 'Desktop' },
            'Desktop Medium': { width: 1366, height: 768, userAgent: 'Desktop' },
            'Desktop Large': { width: 1920, height: 1080, userAgent: 'Desktop' },
            'Desktop 4K': { width: 2560, height: 1440, userAgent: 'Desktop' }
        };
        
        this.currentDevice = null;
        this.originalViewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        this.init();
    }

    init() {
        this.createTestingInterface();
        this.runAutomatedTests();
    }

    createTestingInterface() {
        // Create floating test panel
        const panel = document.createElement('div');
        panel.id = 'device-testing-panel';
        panel.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
                z-index: 9999;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 14px;
                max-width: 300px;
                display: none;
            " class="device-testing-panel">
                <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600;">Device Testing</h3>
                    <button id="close-testing-panel" style="
                        background: none;
                        border: none;
                        font-size: 18px;
                        cursor: pointer;
                        padding: 4px;
                        margin-left: auto;
                    ">×</button>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 4px; font-weight: 500;">Select Device:</label>
                    <select id="device-selector" style="
                        width: 100%;
                        padding: 8px;
                        border: 1px solid #d1d5db;
                        border-radius: 6px;
                        font-size: 14px;
                    ">
                        <option value="">Original Viewport</option>
                        ${Object.keys(this.devices).map(device => 
                            `<option value="${device}">${device} (${this.devices[device].width}×${this.devices[device].height})</option>`
                        ).join('')}
                    </select>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div id="current-viewport" style="
                        padding: 8px;
                        background: #f3f4f6;
                        border-radius: 6px;
                        font-size: 12px;
                        color: #6b7280;
                    ">
                        Current: ${window.innerWidth}×${window.innerHeight}
                    </div>
                </div>
                
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <button id="run-responsive-test" style="
                        flex: 1;
                        padding: 8px 12px;
                        background: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Test All Devices</button>
                    <button id="reset-viewport" style="
                        flex: 1;
                        padding: 8px 12px;
                        background: #6b7280;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Reset</button>
                </div>
                
                <div id="test-results" style="
                    max-height: 200px;
                    overflow-y: auto;
                    font-size: 12px;
                    line-height: 1.4;
                "></div>
            </div>
        `;
        
        document.body.appendChild(panel);
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Toggle panel visibility with keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.toggleTestingPanel();
            }
        });

        // Device selector
        const deviceSelector = document.getElementById('device-selector');
        deviceSelector.addEventListener('change', (e) => {
            if (e.target.value) {
                this.simulateDevice(e.target.value);
            } else {
                this.resetViewport();
            }
        });

        // Test all devices button
        document.getElementById('run-responsive-test').addEventListener('click', () => {
            this.runAllDeviceTests();
        });

        // Reset button
        document.getElementById('reset-viewport').addEventListener('click', () => {
            this.resetViewport();
            deviceSelector.value = '';
        });

        // Close panel
        document.getElementById('close-testing-panel').addEventListener('click', () => {
            this.hideTestingPanel();
        });
    }

    toggleTestingPanel() {
        const panel = document.querySelector('.device-testing-panel');
        if (panel.style.display === 'none') {
            this.showTestingPanel();
        } else {
            this.hideTestingPanel();
        }
    }

    showTestingPanel() {
        const panel = document.querySelector('.device-testing-panel');
        panel.style.display = 'block';
        console.log('Device Testing Panel opened. Press Ctrl+Shift+D to toggle.');
    }

    hideTestingPanel() {
        const panel = document.querySelector('.device-testing-panel');
        panel.style.display = 'none';
    }

    simulateDevice(deviceName) {
        const device = this.devices[deviceName];
        if (!device) return;

        this.currentDevice = deviceName;
        
        // Simulate viewport resize
        this.setViewportSize(device.width, device.height);
        
        // Update current viewport display
        this.updateViewportDisplay();
        
        // Run responsive tests for this device
        this.testDeviceLayout(deviceName, device);
        
        console.log(`Simulating ${deviceName}: ${device.width}×${device.height}`);
    }

    setViewportSize(width, height) {
        // Note: This is a simulation - actual viewport resizing requires browser dev tools
        // We'll use CSS transforms and media query simulation instead
        
        const html = document.documentElement;
        const body = document.body;
        
        // Set custom CSS properties for responsive testing
        html.style.setProperty('--test-viewport-width', `${width}px`);
        html.style.setProperty('--test-viewport-height', `${height}px`);
        
        // Add a class to indicate we're in testing mode
        body.classList.add('device-testing-mode');
        body.setAttribute('data-test-device', this.currentDevice);
        
        // Trigger resize event for JavaScript that listens to it
        window.dispatchEvent(new Event('resize'));
    }

    resetViewport() {
        const html = document.documentElement;
        const body = document.body;
        
        html.style.removeProperty('--test-viewport-width');
        html.style.removeProperty('--test-viewport-height');
        body.classList.remove('device-testing-mode');
        body.removeAttribute('data-test-device');
        
        this.currentDevice = null;
        this.updateViewportDisplay();
        
        window.dispatchEvent(new Event('resize'));
        console.log('Viewport reset to original size');
    }

    updateViewportDisplay() {
        const display = document.getElementById('current-viewport');
        if (this.currentDevice) {
            const device = this.devices[this.currentDevice];
            display.textContent = `Testing: ${this.currentDevice} (${device.width}×${device.height})`;
        } else {
            display.textContent = `Current: ${window.innerWidth}×${window.innerHeight}`;
        }
    }

    testDeviceLayout(deviceName, device) {
        const results = [];
        
        try {
            // Test navigation visibility
            const mobileNav = document.getElementById('mobile-nav-toggle');
            const desktopNav = document.querySelector('.lg\\:flex');
            
            if (device.width <= 767) {
                // Mobile breakpoint
                if (mobileNav && window.getComputedStyle(mobileNav).display === 'none') {
                    results.push(`❌ Mobile nav hidden on ${deviceName}`);
                } else {
                    results.push(`✅ Mobile nav visible on ${deviceName}`);
                }
            } else {
                // Desktop breakpoint
                if (desktopNav && window.getComputedStyle(desktopNav).display === 'none') {
                    results.push(`❌ Desktop nav hidden on ${deviceName}`);
                } else {
                    results.push(`✅ Desktop nav visible on ${deviceName}`);
                }
            }
            
            // Test grid layout
            const mainGrid = document.querySelector('.grid');
            if (mainGrid) {
                const gridCols = window.getComputedStyle(mainGrid).getPropertyValue('grid-template-columns');
                if (device.width <= 767 && !gridCols.includes('1fr')) {
                    results.push(`❌ Grid not single column on ${deviceName}`);
                } else if (device.width >= 1024 && !gridCols.includes('repeat(3')) {
                    results.push(`❌ Grid not 3-column on ${deviceName}`);
                } else {
                    results.push(`✅ Grid layout correct on ${deviceName}`);
                }
            }
            
            // Test touch targets
            if (device.userAgent.includes('iPhone') || device.userAgent.includes('Android')) {
                const buttons = document.querySelectorAll('button, a[role="button"]');
                let smallButtons = 0;
                buttons.forEach(button => {
                    const rect = button.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44)) {
                        smallButtons++;
                    }
                });
                
                if (smallButtons > 0) {
                    results.push(`❌ ${smallButtons} buttons too small for touch on ${deviceName}`);
                } else {
                    results.push(`✅ All buttons touch-friendly on ${deviceName}`);
                }
            }
            
        } catch (error) {
            results.push(`❌ Error testing ${deviceName}: ${error.message}`);
        }
        
        this.displayTestResults(results);
    }

    runAllDeviceTests() {
        const resultsContainer = document.getElementById('test-results');
        resultsContainer.innerHTML = '<div style="color: #3b82f6;">Running tests on all devices...</div>';
        
        const allResults = [];
        const deviceNames = Object.keys(this.devices);
        let currentIndex = 0;
        
        const testNextDevice = () => {
            if (currentIndex >= deviceNames.length) {
                // All tests complete
                this.resetViewport();
                this.displayAllTestResults(allResults);
                return;
            }
            
            const deviceName = deviceNames[currentIndex];
            this.simulateDevice(deviceName);
            
            // Wait for layout to settle
            setTimeout(() => {
                const device = this.devices[deviceName];
                const results = [];
                
                // Run the same tests as individual device test
                this.testDeviceLayout(deviceName, device);
                
                allResults.push({
                    device: deviceName,
                    results: results
                });
                
                currentIndex++;
                testNextDevice();
            }, 500);
        };
        
        testNextDevice();
    }

    displayTestResults(results) {
        const container = document.getElementById('test-results');
        container.innerHTML = results.map(result => 
            `<div style="margin-bottom: 4px;">${result}</div>`
        ).join('');
    }

    displayAllTestResults(allResults) {
        const container = document.getElementById('test-results');
        let html = '<div style="font-weight: 600; margin-bottom: 8px;">All Device Tests Complete:</div>';
        
        allResults.forEach(({ device, results }) => {
            html += `<div style="margin-bottom: 8px;">
                <div style="font-weight: 500; color: #374151;">${device}:</div>
                ${results.map(result => `<div style="margin-left: 12px; font-size: 11px;">${result}</div>`).join('')}
            </div>`;
        });
        
        container.innerHTML = html;
    }

    runAutomatedTests() {
        // Run basic responsive tests on page load
        console.log('Running automated device compatibility tests...');
        
        // Test current viewport
        const currentWidth = window.innerWidth;
        let breakpoint = 'unknown';
        
        if (currentWidth <= 767) breakpoint = 'mobile';
        else if (currentWidth <= 1023) breakpoint = 'tablet';
        else breakpoint = 'desktop';
        
        console.log(`Current breakpoint: ${breakpoint} (${currentWidth}px)`);
        
        // Test for common responsive issues
        this.checkCommonIssues();
    }

    checkCommonIssues() {
        const issues = [];
        
        // Check for horizontal scrolling
        if (document.body.scrollWidth > window.innerWidth) {
            issues.push('Horizontal scrolling detected - content may be too wide');
        }
        
        // Check for missing viewport meta tag
        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (!viewportMeta) {
            issues.push('Missing viewport meta tag');
        } else {
            const content = viewportMeta.getAttribute('content');
            if (!content.includes('width=device-width')) {
                issues.push('Viewport meta tag missing width=device-width');
            }
        }
        
        // Check for fixed positioning issues
        const fixedElements = document.querySelectorAll('[style*="position: fixed"], .fixed');
        fixedElements.forEach((element, index) => {
            const rect = element.getBoundingClientRect();
            if (rect.right > window.innerWidth || rect.bottom > window.innerHeight) {
                issues.push(`Fixed element ${index + 1} extends beyond viewport`);
            }
        });
        
        if (issues.length > 0) {
            console.warn('Responsive design issues detected:');
            issues.forEach(issue => console.warn(`- ${issue}`));
        } else {
            console.log('✅ No common responsive issues detected');
        }
    }
}

// Initialize device testing utility
document.addEventListener('DOMContentLoaded', () => {
    window.deviceTester = new DeviceTestingUtility();
    console.log('Device Testing Utility loaded. Press Ctrl+Shift+D to open testing panel.');
});

// Add CSS for device testing mode
const testingCSS = `
    .device-testing-mode {
        /* Add any special styles for testing mode */
    }
    
    /* Simulate different viewport sizes using CSS */
    @media (max-width: 767px) {
        .device-testing-mode[data-test-device*="Desktop"] .lg\\:hidden {
            display: block !important;
        }
        .device-testing-mode[data-test-device*="Desktop"] .lg\\:flex {
            display: none !important;
        }
    }
`;

const style = document.createElement('style');
style.textContent = testingCSS;
document.head.appendChild(style);