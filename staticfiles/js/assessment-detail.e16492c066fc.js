/**
 * Assessment Detail Page JavaScript
 * Handles interactive functionality for the insurance assessment detail page
 */

// Global assessment data and functionality
let assessmentDetailApp = {
    // Assessment data
    assessmentData: null,
    currentSection: null,

    // Mobile navigation state
    mobileNavOpen: false,

    // Initialize the assessment detail page
    init() {
        this.initializeEventListeners();
        this.initializeMobileNavigation();
        this.initializeAssessmentSections();
        this.initializePhotoGallery();
        this.initializeLoadingStates();
        this.initializeAnimations();
        this.initializeAccessibility();

        console.log('Assessment Detail Page initialized');
    },

    // Initialize event listeners
    initializeEventListeners() {
        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const mobileMenuClose = document.getElementById('mobileMenuClose');
        const mobileNavOverlay = document.getElementById('mobileNavOverlay');

        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => this.toggleMobileNav());
        }

        if (mobileMenuClose) {
            mobileMenuClose.addEventListener('click', () => this.closeMobileNav());
        }

        if (mobileNavOverlay) {
            mobileNavOverlay.addEventListener('click', () => this.closeMobileNav());
        }

        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());

        // Handle escape key for mobile nav
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileNavOpen) {
                this.closeMobileNav();
            }
        });

        // Handle action buttons
        this.initializeActionButtons();
    },

    // Initialize mobile navigation
    initializeMobileNavigation() {
        // Add smooth transitions
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        if (mobileNavMenu) {
            mobileNavMenu.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        }
    },

    // Toggle mobile navigation
    toggleMobileNav() {
        this.mobileNavOpen = !this.mobileNavOpen;
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const mobileNavOverlay = document.getElementById('mobileNavOverlay');

        if (this.mobileNavOpen) {
            this.openMobileNav();
        } else {
            this.closeMobileNav();
        }
    },

    // Open mobile navigation
    openMobileNav() {
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const mobileNavOverlay = document.getElementById('mobileNavOverlay');

        if (mobileNavMenu) {
            mobileNavMenu.classList.add('active');
            mobileNavMenu.setAttribute('aria-hidden', 'false');
        }

        if (mobileNavOverlay) {
            mobileNavOverlay.classList.add('active');
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Focus management
        const firstFocusableElement = mobileNavMenu?.querySelector('a, button, [tabindex]:not([tabindex="-1"])');
        if (firstFocusableElement) {
            firstFocusableElement.focus();
        }
    },

    // Close mobile navigation
    closeMobileNav() {
        this.mobileNavOpen = false;
        const mobileNavMenu = document.getElementById('mobileNavMenu');
        const mobileNavOverlay = document.getElementById('mobileNavOverlay');

        if (mobileNavMenu) {
            mobileNavMenu.classList.remove('active');
            mobileNavMenu.setAttribute('aria-hidden', 'true');
        }

        if (mobileNavOverlay) {
            mobileNavOverlay.classList.remove('active');
        }

        // Restore body scroll
        document.body.style.overflow = '';

        // Return focus to toggle button
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        if (mobileMenuToggle) {
            mobileMenuToggle.focus();
        }
    },

    // Handle window resize
    handleResize() {
        if (window.innerWidth > 768 && this.mobileNavOpen) {
            this.closeMobileNav();
        }
    },

    // Initialize assessment sections
    initializeAssessmentSections() {
        const sectionCards = document.querySelectorAll('.assessment-section-card, .assessment-detail-card[data-section-id]');

        sectionCards.forEach(card => {
            // Add click handler for section navigation
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = card.dataset.sectionId;
                if (sectionId) {
                    this.navigateToSection(sectionId);
                }
            });

            // Add keyboard navigation
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });

            // Make focusable
            if (!card.hasAttribute('tabindex')) {
                card.setAttribute('tabindex', '0');
            }
        });
    },

    // Navigate to specific assessment section
    navigateToSection(sectionId) {
        if (!sectionId) return;

        // Show loading state
        this.showSectionLoading(sectionId);

        // Simulate navigation (in real app, this would be an actual route)
        setTimeout(() => {
            console.log(`Navigating to section: ${sectionId}`);
            // In a real application, this would navigate to the section detail page
            // window.location.href = `/insurance/assessments/${claimId}/section/${sectionId}/`;
        }, 500);
    },

    // Show loading state for section
    showSectionLoading(sectionId) {
        const sectionCard = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (sectionCard) {
            const originalContent = sectionCard.innerHTML;
            sectionCard.innerHTML = `
                <div class="flex items-center justify-center p-4">
                    <div class="assessment-spinner"></div>
                    <span class="ml-2 text-sm text-gray-600">Loading section...</span>
                </div>
            `;

            // Store original content for restoration if needed
            sectionCard.dataset.originalContent = originalContent;
        }
    },

    // Initialize photo gallery
    initializePhotoGallery() {
        const photoItems = document.querySelectorAll('[data-photo-item], .photo-item');

        photoItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                this.openPhotoGallery(index);
            });

            // Add keyboard navigation
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.openPhotoGallery(index);
                }
            });
        });
    },

    // Open photo gallery
    openPhotoGallery(startIndex = 0) {
        console.log(`Opening photo gallery at index: ${startIndex}`);
        // In a real application, this would open a modal or navigate to gallery view
        // For now, just log the action
    },

    // Initialize action buttons
    initializeActionButtons() {
        // Approve settlement button
        const approveBtn = document.querySelector('button:has-text("Approve Settlement"), button:contains("Approve Settlement")');
        if (approveBtn) {
            approveBtn.addEventListener('click', () => this.handleApproveSettlement());
        }

        // Reject claim button
        const rejectBtn = document.querySelector('button:has-text("Reject Claim"), button:contains("Reject Claim")');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => this.handleRejectClaim());
        }

        // Request more info button
        const requestInfoBtn = document.querySelector('button:has-text("Request More Info"), button:contains("Request More Info")');
        if (requestInfoBtn) {
            requestInfoBtn.addEventListener('click', () => this.handleRequestMoreInfo());
        }

        // Send message button
        const sendMessageBtn = document.querySelector('button:has-text("Send Message"), button:contains("Send Message")');
        if (sendMessageBtn) {
            sendMessageBtn.addEventListener('click', () => this.handleSendMessage());
        }

        // Schedule call button
        const scheduleCallBtn = document.querySelector('button:has-text("Schedule Call"), button:contains("Schedule Call")');
        if (scheduleCallBtn) {
            scheduleCallBtn.addEventListener('click', () => this.handleScheduleCall());
        }

        // Generate settlement letter button
        const generateLetterBtn = document.querySelector('button:has-text("Generate Settlement Letter"), button:contains("Generate Settlement Letter")');
        if (generateLetterBtn) {
            generateLetterBtn.addEventListener('click', () => this.handleGenerateSettlementLetter());
        }
    },

    // Handle approve settlement
    handleApproveSettlement() {
        if (confirm('Are you sure you want to approve this settlement?')) {
            this.showLoadingState('Processing settlement approval...');

            // Simulate API call
            setTimeout(() => {
                this.hideLoadingState();
                this.showSuccessMessage('Settlement approved successfully!');
            }, 2000);
        }
    },

    // Handle reject claim
    handleRejectClaim() {
        if (confirm('Are you sure you want to reject this claim?')) {
            this.showLoadingState('Processing claim rejection...');

            // Simulate API call
            setTimeout(() => {
                this.hideLoadingState();
                this.showErrorMessage('Claim rejected successfully!');
            }, 2000);
        }
    },

    // Handle request more info
    handleRequestMoreInfo() {
        this.showLoadingState('Sending request for more information...');

        setTimeout(() => {
            this.hideLoadingState();
            this.showSuccessMessage('Request for more information sent!');
        }, 1500);
    },

    // Handle send message
    handleSendMessage() {
        this.showLoadingState('Sending message...');

        setTimeout(() => {
            this.hideLoadingState();
            this.showSuccessMessage('Message sent successfully!');
        }, 1000);
    },

    // Handle schedule call
    handleScheduleCall() {
        this.showLoadingState('Scheduling call...');

        setTimeout(() => {
            this.hideLoadingState();
            this.showSuccessMessage('Call scheduled successfully!');
        }, 1500);
    },

    // Handle generate settlement letter
    handleGenerateSettlementLetter() {
        this.showLoadingState('Generating settlement letter...');

        setTimeout(() => {
            this.hideLoadingState();
            this.showSuccessMessage('Settlement letter generated successfully!');
        }, 2000);
    },

    // Show loading state
    showLoadingState(message = 'Processing...') {
        // Create or update loading overlay
        let loadingOverlay = document.getElementById('assessment-loading-overlay');

        if (!loadingOverlay) {
            loadingOverlay = document.createElement('div');
            loadingOverlay.id = 'assessment-loading-overlay';
            loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            loadingOverlay.innerHTML = `
                <div class="bg-white rounded-lg p-6 flex items-center space-x-4">
                    <div class="assessment-spinner"></div>
                    <span class="text-gray-700">${message}</span>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
        } else {
            loadingOverlay.querySelector('span').textContent = message;
            loadingOverlay.classList.remove('hidden');
        }

        // Prevent interaction
        document.body.style.pointerEvents = 'none';
        loadingOverlay.style.pointerEvents = 'auto';
    },

    // Hide loading state
    hideLoadingState() {
        const loadingOverlay = document.getElementById('assessment-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }

        // Restore interaction
        document.body.style.pointerEvents = '';
    },

    // Show success message
    showSuccessMessage(message) {
        this.showNotification(message, 'success');
    },

    // Show error message
    showErrorMessage(message) {
        this.showNotification(message, 'error');
    },

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;

        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    },

    // Initialize loading states for buttons
    initializeLoadingStates() {
        const buttonsWithLoading = document.querySelectorAll('[data-loading]');

        buttonsWithLoading.forEach(button => {
            button.addEventListener('click', (e) => {
                const loadingText = button.dataset.loadingText || 'Loading...';
                const originalText = button.textContent;

                button.disabled = true;
                button.innerHTML = `<div class="assessment-spinner w-4 h-4 mr-2"></div>${loadingText}`;

                // Re-enable after 3 seconds (or when loading is complete)
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = originalText;
                }, 3000);
            });
        });
    },

    // Initialize animations
    initializeAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements that should animate
        const animateElements = document.querySelectorAll('.assessment-detail-card, .assessment-section-card');
        animateElements.forEach(el => {
            observer.observe(el);
        });
    },

    // Initialize accessibility features
    initializeAccessibility() {
        // Add ARIA labels where needed
        const sectionCards = document.querySelectorAll('.assessment-section-card');
        sectionCards.forEach(card => {
            const sectionName = card.querySelector('h3')?.textContent || 'Assessment Section';
            card.setAttribute('aria-label', `Navigate to ${sectionName} details`);
            card.setAttribute('role', 'button');
        });

        // Add skip links
        this.addSkipLinks();

        // Improve focus management
        this.improveFocusManagement();
    },

    // Add skip links for accessibility
    addSkipLinks() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white p-2 rounded z-50';
        document.body.insertBefore(skipLink, document.body.firstChild);
    },

    // Improve focus management
    improveFocusManagement() {
        // Add focus indicators
        const focusableElements = document.querySelectorAll('button, a, [tabindex="0"]');
        focusableElements.forEach(el => {
            el.addEventListener('focus', () => {
                el.classList.add('focus-ring');
            });

            el.addEventListener('blur', () => {
                el.classList.remove('focus-ring');
            });
        });
    }
};

// Global function for section navigation (called from onclick handlers)
function viewSection(sectionId) {
    assessmentDetailApp.navigateToSection(sectionId);
}

// Global function for photo viewing
function viewPhoto(photoId) {
    assessmentDetailApp.openPhotoGallery(photoId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    assessmentDetailApp.init();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = assessmentDetailApp;
}
