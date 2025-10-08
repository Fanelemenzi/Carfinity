/**
 * Assessment Dashboard Filters
 * Enhanced filtering and organization support for the assessment dashboard
 */

class AssessmentDashboardFilters {
    constructor() {
        this.initializeFilters();
        this.initializeOrganizationSupport();
    }

    initializeFilters() {
        // Enhanced filter initialization
        console.log('Assessment Dashboard Filters initialized');
    }

    initializeOrganizationSupport() {
        // Organization-specific functionality
        const organizationFilter = document.getElementById('organizationFilter');
        
        if (organizationFilter) {
            organizationFilter.addEventListener('change', (e) => {
                this.handleOrganizationFilter(e.target.value);
            });
        }
    }

    handleOrganizationFilter(organizationId) {
        // Handle organization filtering
        const tableRows = document.querySelectorAll('#claimsTableBody tr[data-claim-id]');
        let visibleCount = 0;

        tableRows.forEach(row => {
            const rowOrganization = row.dataset.organization;
            
            if (!organizationId || rowOrganization === organizationId) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        this.updateFilterCount(visibleCount, tableRows.length);
    }

    updateFilterCount(visible, total) {
        const countElement = document.querySelector('.filter-count');
        if (countElement) {
            if (visible === total) {
                countElement.textContent = `Showing ${total} assessment${total !== 1 ? 's' : ''}`;
            } else {
                countElement.textContent = `Showing ${visible} of ${total} assessments (filtered)`;
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AssessmentDashboardFilters();
});