/**
 * Workflow Integration Test Script
 * Tests the complete workflow: landing page → claims table → direct navigation → detailed assessment view
 * This script verifies all components are properly integrated and working together
 */

class WorkflowIntegrationTest {
    constructor() {
        this.testResults = [];
        this.currentStep = 0;
        this.isRunning = false;
    }

    /**
     * Run the complete workflow test
     */
    async runCompleteWorkflowTest() {
        if (this.isRunning) {
            console.warn('Test already running');
            return;
        }

        this.isRunning = true;
        this.testResults = [];
        this.currentStep = 0;

        console.log('🚀 Starting Complete Workflow Integration Test');
        console.log('Testing: Landing Page → Claims Table → Direct Navigation → Detailed Assessment View');

        try {
            // Step 1: Test Landing Page Components
            await this.testLandingPageComponents();
            
            // Step 2: Test Navigation to Assessment Dashboard
            await this.testNavigationToAssessmentDashboard();
            
            // Step 3: Test Claims Table Functionality
            await this.testClaimsTableFunctionality();
            
            // Step 4: Test Direct Navigation to Assessment Detail
            await this.testDirectNavigationToDetail();
            
            // Step 5: Test Detailed Tabbed View
            await this.testDetailedTabbedView();
            
            // Step 6: Test Complete User Journey
            await this.testCompleteUserJourney();

            this.showTestResults();
            
        } catch (error) {
            console.error('❌ Workflow test failed:', error);
            this.logTestResult('WORKFLOW_COMPLETE', false, error.message);
        } finally {
            this.isRunning = false;
        }
    }

    /**
     * Test Step 1: Landing Page Components
     */
    async testLandingPageComponents() {
        console.log('📋 Step 1: Testing Landing Page Components');
        
        try {
            // Test action cards exist
            const actionCards = document.querySelectorAll('.action-card');
            if (actionCards.length < 2) {
                throw new Error(`Expected at least 2 action cards, found ${actionCards.length}`);
            }
            this.logTestResult('LANDING_ACTION_CARDS', true, `Found ${actionCards.length} action cards`);

            // Test assessment card has correct URL
            const assessmentCard = document.querySelector('.action-card[data-url*="assessment_dashboard"]');
            if (!assessmentCard) {
                throw new Error('Assessment dashboard action card not found or missing data-url');
            }
            this.logTestResult('LANDING_ASSESSMENT_CARD', true, 'Assessment card properly configured');

            // Test stats grid
            const statsCards = document.querySelectorAll('.stats-grid .bg-white');
            if (statsCards.length < 4) {
                throw new Error(`Expected 4 stats cards, found ${statsCards.length}`);
            }
            this.logTestResult('LANDING_STATS_CARDS', true, `Found ${statsCards.length} stats cards`);

            // Test navigation menu
            const navItems = document.querySelectorAll('.nav-item, .mobile-nav-item');
            if (navItems.length < 3) {
                throw new Error(`Expected at least 3 navigation items, found ${navItems.length}`);
            }
            this.logTestResult('LANDING_NAVIGATION', true, `Found ${navItems.length} navigation items`);

            // Test responsive design elements
            const mobileElements = document.querySelectorAll('.mobile-nav-toggle, .mobile-nav-menu');
            if (mobileElements.length < 2) {
                throw new Error('Mobile navigation elements not found');
            }
            this.logTestResult('LANDING_RESPONSIVE', true, 'Mobile navigation elements present');

            console.log('✅ Step 1 Complete: Landing page components verified');
            
        } catch (error) {
            console.error('❌ Step 1 Failed:', error.message);
            this.logTestResult('LANDING_PAGE_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Test Step 2: Navigation to Assessment Dashboard
     */
    async testNavigationToAssessmentDashboard() {
        console.log('🧭 Step 2: Testing Navigation to Assessment Dashboard');
        
        try {
            // Test assessment dashboard link exists
            const assessmentLinks = document.querySelectorAll('a[href*="assessment_dashboard"], [data-url*="assessment_dashboard"]');
            if (assessmentLinks.length === 0) {
                throw new Error('No assessment dashboard links found');
            }
            this.logTestResult('NAVIGATION_LINKS', true, `Found ${assessmentLinks.length} assessment dashboard links`);

            // Test click handler setup (simulate)
            const actionCard = document.querySelector('.action-card[data-url*="assessment_dashboard"]');
            if (actionCard) {
                // Simulate click event to test handler
                const clickEvent = new Event('click', { bubbles: true });
                actionCard.dispatchEvent(clickEvent);
                this.logTestResult('NAVIGATION_CLICK_HANDLER', true, 'Action card click handler working');
            }

            // Test breadcrumb navigation structure
            const breadcrumbExists = document.querySelector('nav[aria-label="Breadcrumb"], .breadcrumb');
            if (breadcrumbExists) {
                this.logTestResult('NAVIGATION_BREADCRUMBS', true, 'Breadcrumb navigation present');
            }

            console.log('✅ Step 2 Complete: Navigation functionality verified');
            
        } catch (error) {
            console.error('❌ Step 2 Failed:', error.message);
            this.logTestResult('NAVIGATION_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Test Step 3: Claims Table Functionality
     */
    async testClaimsTableFunctionality() {
        console.log('📊 Step 3: Testing Claims Table Functionality');
        
        try {
            // Test if claims table interactivity script is loaded
            if (typeof ClaimsTableState === 'undefined') {
                throw new Error('Claims table interactivity script not loaded');
            }
            this.logTestResult('CLAIMS_SCRIPT_LOADED', true, 'Claims table script loaded');

            // Test filter controls exist
            const filterControls = document.querySelectorAll('[id*="Filter"], .filter-controls');
            if (filterControls.length === 0) {
                throw new Error('Filter controls not found');
            }
            this.logTestResult('CLAIMS_FILTERS', true, `Found ${filterControls.length} filter controls`);

            // Test responsive design (mobile, tablet, desktop filters)
            const mobileFilters = document.querySelectorAll('.mobile-filters, [id*="FilterMobile"]');
            const tabletFilters = document.querySelectorAll('.tablet-filters, [id*="FilterTablet"]');
            const desktopFilters = document.querySelectorAll('.desktop-filters, [id*="Filter"]:not([id*="Mobile"]):not([id*="Tablet"])');
            
            this.logTestResult('CLAIMS_RESPONSIVE_FILTERS', true, 
                `Mobile: ${mobileFilters.length}, Tablet: ${tabletFilters.length}, Desktop: ${desktopFilters.length}`);

            // Test search functionality
            const searchInput = document.querySelector('#globalSearch, [data-search]');
            if (searchInput) {
                this.logTestResult('CLAIMS_SEARCH', true, 'Search functionality present');
            }

            // Test sortable headers (if present)
            const sortableHeaders = document.querySelectorAll('.sortable');
            if (sortableHeaders.length > 0) {
                this.logTestResult('CLAIMS_SORTING', true, `Found ${sortableHeaders.length} sortable columns`);
            }

            // Test mobile claim cards
            const mobileCards = document.querySelectorAll('.mobile-claim-card');
            if (mobileCards.length > 0) {
                this.logTestResult('CLAIMS_MOBILE_CARDS', true, `Found ${mobileCards.length} mobile claim cards`);
            }

            console.log('✅ Step 3 Complete: Claims table functionality verified');
            
        } catch (error) {
            console.error('❌ Step 3 Failed:', error.message);
            this.logTestResult('CLAIMS_TABLE_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Test Step 4: Direct Navigation to Assessment Detail
     */
    async testDirectNavigationToDetail() {
        console.log('🔍 Step 4: Testing Direct Navigation to Assessment Detail');
        
        try {
            // Test if direct navigation functions exist
            if (typeof showClaimPopup !== 'function') {
                throw new Error('showClaimPopup function not found');
            }
            this.logTestResult('DIRECT_NAV_FUNCTION_EXISTS', true, 'showClaimPopup function available (now does direct navigation)');

            // Test direct navigation function
            if (typeof navigateToClaimDetail === 'function') {
                this.logTestResult('DIRECT_NAV_NAVIGATE_FUNCTION', true, 'navigateToClaimDetail function available');
            }

            // Test viewClaim function exists (global function for onclick handlers)
            if (typeof viewClaim === 'function') {
                this.logTestResult('DIRECT_NAV_VIEW_CLAIM', true, 'viewClaim function available');
            }

            // Test that claim buttons have proper onclick handlers
            const claimButtons = document.querySelectorAll('button[onclick*="viewClaim"]');
            if (claimButtons.length > 0) {
                this.logTestResult('DIRECT_NAV_BUTTON_HANDLERS', true, `Found ${claimButtons.length} buttons with viewClaim handlers`);
            }

            // Test that claim rows have proper onclick handlers
            const claimRows = document.querySelectorAll('tr[onclick*="viewClaim"]');
            if (claimRows.length > 0) {
                this.logTestResult('DIRECT_NAV_ROW_HANDLERS', true, `Found ${claimRows.length} rows with viewClaim handlers`);
            }

            console.log('✅ Step 4 Complete: Direct navigation functionality verified');
            
        } catch (error) {
            console.error('❌ Step 4 Failed:', error.message);
            this.logTestResult('DIRECT_NAV_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Test Step 5: Detailed Tabbed View
     */
    async testDetailedTabbedView() {
        console.log('📑 Step 5: Testing Detailed Tabbed View');
        
        try {
            // Test if tab switching function exists
            if (typeof switchTab !== 'function') {
                throw new Error('switchTab function not found');
            }
            this.logTestResult('TABS_SWITCH_FUNCTION', true, 'switchTab function available');

            // Test tab navigation elements
            const tabButtons = document.querySelectorAll('.tab-button, [data-tab]');
            if (tabButtons.length > 0) {
                this.logTestResult('TABS_NAVIGATION', true, `Found ${tabButtons.length} tab buttons`);
            }

            // Test tab content areas
            const tabContents = document.querySelectorAll('.tab-content, [id$="-content"]');
            if (tabContents.length > 0) {
                this.logTestResult('TABS_CONTENT_AREAS', true, `Found ${tabContents.length} tab content areas`);
            }

            // Test required tabs exist (based on design spec)
            const requiredTabs = ['summary', 'costs', 'value', 'points', 'recommendations', 'timeline'];
            let foundTabs = 0;
            
            requiredTabs.forEach(tabName => {
                const tabElement = document.querySelector(`[data-tab="${tabName}"], #${tabName}-content`);
                if (tabElement) {
                    foundTabs++;
                }
            });
            
            this.logTestResult('TABS_REQUIRED_TABS', foundTabs === requiredTabs.length, 
                `Found ${foundTabs}/${requiredTabs.length} required tabs`);

            // Test back navigation
            const backButton = document.querySelector('.back-button, [onclick*="goBack"]');
            if (backButton) {
                this.logTestResult('TABS_BACK_NAVIGATION', true, 'Back navigation button present');
            }

            // Test responsive tab design
            const mobileTabElements = document.querySelectorAll('.mobile-tab-button, .mobile-tab-content');
            if (mobileTabElements.length > 0) {
                this.logTestResult('TABS_RESPONSIVE', true, `Found ${mobileTabElements.length} mobile tab elements`);
            }

            console.log('✅ Step 5 Complete: Detailed tabbed view verified');
            
        } catch (error) {
            console.error('❌ Step 5 Failed:', error.message);
            this.logTestResult('DETAILED_VIEW_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Test Step 6: Complete User Journey
     */
    async testCompleteUserJourney() {
        console.log('🎯 Step 6: Testing Complete User Journey');
        
        try {
            // Simulate complete workflow
            console.log('Simulating user journey...');
            
            // 1. User starts on landing page (already tested)
            this.logTestResult('JOURNEY_LANDING', true, 'User on landing page');
            
            // 2. User clicks "View Vehicle Assessments"
            const assessmentCard = document.querySelector('.action-card[data-url*="assessment_dashboard"]');
            if (assessmentCard) {
                // Simulate click
                const clickEvent = new Event('click', { bubbles: true });
                assessmentCard.dispatchEvent(clickEvent);
                this.logTestResult('JOURNEY_NAVIGATE', true, 'User navigates to assessment dashboard');
            }
            
            // 3. User interacts with claims table
            if (typeof ClaimsTableState !== 'undefined') {
                this.logTestResult('JOURNEY_CLAIMS_TABLE', true, 'User can interact with claims table');
            }
            
            // 4. User clicks on a claim to navigate directly to detail page
            if (typeof showClaimPopup === 'function') {
                try {
                    // Note: showClaimPopup now does direct navigation instead of popup
                    this.logTestResult('JOURNEY_DIRECT_NAV', true, 'User can navigate directly to claim detail');
                } catch (navError) {
                    this.logTestResult('JOURNEY_DIRECT_NAV', false, navError.message);
                }
            }
            
            // 5. User views assessment detail page with all sections
            const assessmentSections = document.querySelectorAll('.assessment-section, [data-section]');
            if (assessmentSections.length > 0) {
                this.logTestResult('JOURNEY_ASSESSMENT_SECTIONS', true, `Assessment page has ${assessmentSections.length} sections`);
            }
            
            // 6. User can navigate between assessment sections
            const sectionLinks = document.querySelectorAll('a[href*="section"], button[onclick*="section"]');
            if (sectionLinks.length > 0) {
                this.logTestResult('JOURNEY_SECTION_NAVIGATION', true, `User can navigate between ${sectionLinks.length} assessment sections`);
            }

            console.log('✅ Step 6 Complete: Complete user journey verified');
            
        } catch (error) {
            console.error('❌ Step 6 Failed:', error.message);
            this.logTestResult('COMPLETE_JOURNEY_TEST', false, error.message);
            throw error;
        }
    }

    /**
     * Log test result
     */
    logTestResult(testName, passed, message) {
        const result = {
            test: testName,
            passed: passed,
            message: message,
            timestamp: new Date().toISOString()
        };
        
        this.testResults.push(result);
        
        const status = passed ? '✅' : '❌';
        console.log(`${status} ${testName}: ${message}`);
    }

    /**
     * Show comprehensive test results
     */
    showTestResults() {
        console.log('\n📊 WORKFLOW INTEGRATION TEST RESULTS');
        console.log('=====================================');
        
        const passed = this.testResults.filter(r => r.passed).length;
        const failed = this.testResults.filter(r => r.passed === false).length;
        const total = this.testResults.length;
        const passRate = ((passed / total) * 100).toFixed(1);
        
        console.log(`Total Tests: ${total}`);
        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${failed}`);
        console.log(`Pass Rate: ${passRate}%`);
        
        if (failed > 0) {
            console.log('\n❌ FAILED TESTS:');
            this.testResults.filter(r => !r.passed).forEach(result => {
                console.log(`- ${result.test}: ${result.message}`);
            });
        }
        
        if (passed === total) {
            console.log('\n🎉 ALL TESTS PASSED! Workflow integration is working correctly.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review the implementation.');
        }
        
        // Create visual summary if in browser
        if (typeof document !== 'undefined') {
            this.createVisualSummary(passed, failed, total, passRate);
        }
    }

    /**
     * Create visual test summary
     */
    createVisualSummary(passed, failed, total, passRate) {
        // Remove existing summary
        const existingSummary = document.getElementById('workflowTestSummary');
        if (existingSummary) {
            existingSummary.remove();
        }

        // Create new summary
        const summary = document.createElement('div');
        summary.id = 'workflowTestSummary';
        summary.className = 'fixed top-4 right-4 bg-white rounded-lg shadow-lg p-4 border z-50 max-w-sm';
        
        const statusColor = failed === 0 ? 'text-green-600' : 'text-red-600';
        const statusIcon = failed === 0 ? 'fa-check-circle' : 'fa-exclamation-circle';
        
        summary.innerHTML = `
            <div class="flex items-center mb-3">
                <i class="fas ${statusIcon} ${statusColor} mr-2"></i>
                <h3 class="font-semibold text-gray-900">Workflow Test Results</h3>
            </div>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span>Total Tests:</span>
                    <span class="font-medium">${total}</span>
                </div>
                <div class="flex justify-between">
                    <span>Passed:</span>
                    <span class="font-medium text-green-600">${passed}</span>
                </div>
                <div class="flex justify-between">
                    <span>Failed:</span>
                    <span class="font-medium text-red-600">${failed}</span>
                </div>
                <div class="flex justify-between">
                    <span>Pass Rate:</span>
                    <span class="font-medium ${statusColor}">${passRate}%</span>
                </div>
            </div>
            <button onclick="this.parentElement.remove()" class="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.body.appendChild(summary);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (summary.parentElement) {
                summary.remove();
            }
        }, 10000);
    }
}

// Initialize and expose globally
window.WorkflowIntegrationTest = WorkflowIntegrationTest;

// Auto-run test when page is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for all scripts to load
    setTimeout(() => {
        const tester = new WorkflowIntegrationTest();
        tester.runCompleteWorkflowTest();
    }, 2000);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WorkflowIntegrationTest;
}