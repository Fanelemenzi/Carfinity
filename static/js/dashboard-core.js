/**
 * Core Dashboard JavaScript Functionality
 * Handles vehicle switching, carousel navigation, and mobile menu interactions
 * Requirements: 2.5, 3.2, 7.1
 */

class DashboardCore {
    constructor() {
        this.currentVehicleId = null;
        this.carouselInterval = null;
        this.carouselCurrentIndex = 0;
        this.carouselAutoRotateDelay = 5000; // 5 seconds
        this.isLoading = false;
        this.touchStartX = 0;
        this.touchEndX = 0;
        
        this.init();
    }
    
    init() {
        this.setupVehicleSwitching();
        this.setupCarouselNavigation();
        this.setupMobileMenuHandling();
        this.setupEventListeners();
        
        console.log('Dashboard core functionality initialized');
    }
    
    /**
     * Vehicle Switching AJAX Functionality
     * Requirement 2.5: Dynamic vehicle switching with loading states
     */
    setupVehicleSwitching() {
        // Get all vehicle selectors
        const vehicleSelectors = document.querySelectorAll('#vehicle-selector, #mobile-vehicle-selector, #vehicle-overview-selector');
        
        vehicleSelectors.forEach(selector => {
            if (selector) {
                // Store initial vehicle ID
                this.currentVehicleId = selector.value;
                
                selector.addEventListener('change', (e) => {
                    this.handleVehicleSwitch(e.target.value, selector);
                });
            }
        });
    }
    
    async handleVehicleSwitch(newVehicleId, triggerSelector) {
        if (this.isLoading || newVehicleId === this.currentVehicleId) {
            return;
        }
        
        this.isLoading = true;
        this.showVehicleLoadingState(triggerSelector);
        
        try {
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                             document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            // Make AJAX request to switch vehicle
            const response = await fetch('/dashboard/switch-vehicle/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    vehicle_id: newVehicleId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Update dashboard with new vehicle data
                this.updateDashboardData(data.vehicle_data);
                this.currentVehicleId = newVehicleId;
                
                // Sync all vehicle selectors
                this.syncVehicleSelectors(newVehicleId);
                
                // Show success feedback
                this.showSuccessMessage('Vehicle switched successfully');
                
                // Announce to screen readers
                this.announceToScreenReader(`Switched to ${data.vehicle_data.make} ${data.vehicle_data.model}`);
                
            } else {
                throw new Error(data.error || 'Failed to switch vehicle');
            }
            
        } catch (error) {
            console.error('Vehicle switch error:', error);
            this.showErrorMessage('Failed to switch vehicle. Please try again.');
            
            // Revert selector to previous value
            triggerSelector.value = this.currentVehicleId;
            
        } finally {
            this.hideVehicleLoadingState(triggerSelector);
            this.isLoading = false;
        }
    }
    
    updateDashboardData(vehicleData) {
        // Update vehicle overview card
        this.updateVehicleOverview(vehicleData);
        
        // Update service information
        this.updateServiceInfo(vehicleData);
        
        // Update cost analytics
        this.updateCostAnalytics(vehicleData);
        
        // Trigger dashboard refresh animations
        this.triggerRefreshAnimations();
    }
    
    updateVehicleOverview(vehicleData) {
        // Update vehicle title
        const vehicleTitle = document.querySelector('.vehicle-overview h3, .vehicle-title');
        if (vehicleTitle) {
            vehicleTitle.textContent = `${vehicleData.manufacture_year} ${vehicleData.make} ${vehicleData.model}`;
        }
        
        // Update VIN display
        const vinDisplay = document.querySelector('.vin-display, [class*="vin"]');
        if (vinDisplay && vehicleData.vin) {
            vinDisplay.textContent = `VIN: ${vehicleData.vin.slice(0, 8)}...`;
        }
        
        // Update mileage
        const mileageDisplay = document.querySelector('.mileage-display, [class*="mileage"]');
        if (mileageDisplay && vehicleData.current_mileage) {
            mileageDisplay.textContent = `${parseInt(vehicleData.current_mileage).toLocaleString()} mi`;
        }
        
        // Update vehicle image if provided
        const vehicleImage = document.querySelector('.vehicle-image img, .vehicle-overview img');
        if (vehicleImage && vehicleData.image_url) {
            vehicleImage.src = vehicleData.image_url;
            vehicleImage.alt = `${vehicleData.make} ${vehicleData.model}`;
        }
        
        // Update health status
        if (vehicleData.health_status) {
            this.updateHealthStatus(vehicleData.health_status);
        }
        
        // Update next service information
        if (vehicleData.next_service) {
            this.updateNextService(vehicleData.next_service);
        }
        
        // Update estimated value
        if (vehicleData.estimated_value) {
            this.updateEstimatedValue(vehicleData.estimated_value);
        }
    }
    
    updateHealthStatus(healthData) {
        const healthScore = document.querySelector('.health-score, [data-health]');
        const healthBar = document.querySelector('.health-bar .bg-green-600, .progress-bar');
        const healthText = document.querySelector('.health-status-text');
        
        if (healthScore) {
            healthScore.textContent = `${healthData.score}%`;
        }
        
        if (healthBar) {
            healthBar.style.width = `${healthData.score}%`;
        }
        
        if (healthText) {
            healthText.textContent = healthData.status || 'Good';
        }
    }
    
    updateNextService(serviceData) {
        const serviceTitle = document.querySelector('.next-service-title');
        const serviceDate = document.querySelector('.next-service-date');
        const serviceMileage = document.querySelector('.next-service-mileage');
        
        if (serviceTitle) {
            serviceTitle.textContent = serviceData.type || 'Oil Change & Inspection';
        }
        
        if (serviceDate && serviceData.due_date) {
            serviceDate.textContent = `Due: ${serviceData.due_date}`;
        }
        
        if (serviceMileage && serviceData.due_mileage) {
            serviceMileage.textContent = `or ${parseInt(serviceData.due_mileage).toLocaleString()} mi`;
        }
    }
    
    updateEstimatedValue(valueData) {
        const valueAmount = document.querySelector('.estimated-value-amount');
        const valueChange = document.querySelector('.value-change');
        
        if (valueAmount) {
            valueAmount.textContent = `$${parseInt(valueData.amount).toLocaleString()}`;
        }
        
        if (valueChange && valueData.change_percent) {
            const isPositive = valueData.change_percent > 0;
            valueChange.innerHTML = `
                <i class="fas fa-arrow-${isPositive ? 'up' : 'down'} text-${isPositive ? 'green' : 'red'}-500 text-xs"></i>
                <span class="text-xs font-medium text-${isPositive ? 'green' : 'red'}-600">${isPositive ? '+' : ''}${valueData.change_percent}%</span>
            `;
        }
    }
    
    syncVehicleSelectors(vehicleId) {
        const selectors = document.querySelectorAll('#vehicle-selector, #mobile-vehicle-selector, #vehicle-overview-selector');
        selectors.forEach(selector => {
            if (selector.value !== vehicleId) {
                selector.value = vehicleId;
            }
        });
    }
    
    showVehicleLoadingState(selector) {
        const loadingIndicator = selector.parentElement.querySelector('[id*="loading"]');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('hidden');
        }
        
        selector.disabled = true;
        selector.style.opacity = '0.6';
    }
    
    hideVehicleLoadingState(selector) {
        const loadingIndicator = selector.parentElement.querySelector('[id*="loading"]');
        if (loadingIndicator) {
            loadingIndicator.classList.add('hidden');
        }
        
        selector.disabled = false;
        selector.style.opacity = '1';
    }
    
    /**
     * Carousel Auto-rotation and Navigation Logic
     * Requirement 3.2: Interactive carousel with auto-rotation
     */
    setupCarouselNavigation() {
        const carousel = document.querySelector('#promotions-carousel, [data-carousel]');
        if (!carousel) return;
        
        const carouselTrack = carousel.querySelector('#carousel-track, .carousel-track');
        const prevButton = document.querySelector('#carousel-prev');
        const nextButton = document.querySelector('#carousel-next');
        const dots = document.querySelectorAll('.carousel-dot');
        
        if (!carouselTrack) return;
        
        const slides = carouselTrack.querySelectorAll('.carousel-slide, [data-carousel-item]');
        this.carouselTotalSlides = slides.length;
        
        // Set initial state
        this.carouselCurrentIndex = parseInt(carousel.dataset.currentIndex) || 0;
        this.updateCarouselPosition();
        
        // Setup navigation buttons
        if (prevButton) {
            prevButton.addEventListener('click', () => this.navigateCarousel('prev'));
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => this.navigateCarousel('next'));
        }
        
        // Setup dot indicators
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => this.goToSlide(index));
        });
        
        // Setup touch/swipe gestures
        this.setupCarouselTouchGestures(carousel);
        
        // Start auto-rotation
        this.startCarouselAutoRotation();
        
        // Pause auto-rotation on hover
        carousel.addEventListener('mouseenter', () => this.pauseCarouselAutoRotation());
        carousel.addEventListener('mouseleave', () => this.startCarouselAutoRotation());
        
        // Pause auto-rotation on focus (accessibility)
        carousel.addEventListener('focusin', () => this.pauseCarouselAutoRotation());
        carousel.addEventListener('focusout', () => this.startCarouselAutoRotation());
    }
    
    navigateCarousel(direction) {
        if (direction === 'next') {
            this.carouselCurrentIndex = (this.carouselCurrentIndex + 1) % this.carouselTotalSlides;
        } else {
            this.carouselCurrentIndex = this.carouselCurrentIndex === 0 ? 
                this.carouselTotalSlides - 1 : this.carouselCurrentIndex - 1;
        }
        
        this.updateCarouselPosition();
        this.announceCarouselChange();
        
        // Reset auto-rotation timer
        this.resetCarouselAutoRotation();
    }
    
    goToSlide(index) {
        if (index >= 0 && index < this.carouselTotalSlides) {
            this.carouselCurrentIndex = index;
            this.updateCarouselPosition();
            this.announceCarouselChange();
            this.resetCarouselAutoRotation();
        }
    }
    
    updateCarouselPosition() {
        const carousel = document.querySelector('#promotions-carousel, [data-carousel]');
        const carouselTrack = carousel?.querySelector('#carousel-track, .carousel-track');
        
        if (!carouselTrack) return;
        
        // Calculate slide width based on responsive design
        const slideWidth = this.getSlideWidth();
        const offset = -this.carouselCurrentIndex * slideWidth;
        
        carouselTrack.style.transform = `translateX(${offset}px)`;
        
        // Update carousel data attribute
        if (carousel) {
            carousel.dataset.currentIndex = this.carouselCurrentIndex;
        }
        
        // Update dot indicators
        this.updateCarouselDots();
    }
    
    getSlideWidth() {
        const carousel = document.querySelector('#promotions-carousel, [data-carousel]');
        if (!carousel) return 0;
        
        const containerWidth = carousel.offsetWidth;
        
        // Responsive slide widths
        if (window.innerWidth >= 1024) {
            return containerWidth / 3; // 3 slides on desktop
        } else if (window.innerWidth >= 640) {
            return containerWidth / 2; // 2 slides on tablet
        } else {
            return containerWidth; // 1 slide on mobile
        }
    }
    
    updateCarouselDots() {
        const dots = document.querySelectorAll('.carousel-dot');
        dots.forEach((dot, index) => {
            if (index === this.carouselCurrentIndex) {
                dot.classList.add('bg-indigo-600');
                dot.classList.remove('bg-gray-300');
                dot.setAttribute('aria-current', 'true');
            } else {
                dot.classList.remove('bg-indigo-600');
                dot.classList.add('bg-gray-300');
                dot.removeAttribute('aria-current');
            }
        });
    }
    
    setupCarouselTouchGestures(carousel) {
        carousel.addEventListener('touchstart', (e) => {
            this.touchStartX = e.touches[0].clientX;
            this.pauseCarouselAutoRotation();
        }, { passive: true });
        
        carousel.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].clientX;
            this.handleCarouselSwipe();
            this.startCarouselAutoRotation();
        }, { passive: true });
    }
    
    handleCarouselSwipe() {
        const swipeThreshold = 50;
        const swipeDistance = this.touchStartX - this.touchEndX;
        
        if (Math.abs(swipeDistance) > swipeThreshold) {
            if (swipeDistance > 0) {
                this.navigateCarousel('next');
            } else {
                this.navigateCarousel('prev');
            }
            
            // Haptic feedback if available
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }
    
    startCarouselAutoRotation() {
        this.pauseCarouselAutoRotation(); // Clear any existing interval
        
        this.carouselInterval = setInterval(() => {
            this.navigateCarousel('next');
        }, this.carouselAutoRotateDelay);
    }
    
    pauseCarouselAutoRotation() {
        if (this.carouselInterval) {
            clearInterval(this.carouselInterval);
            this.carouselInterval = null;
        }
    }
    
    resetCarouselAutoRotation() {
        this.pauseCarouselAutoRotation();
        this.startCarouselAutoRotation();
    }
    
    announceCarouselChange() {
        const currentSlide = document.querySelector(`[data-carousel-item]:nth-child(${this.carouselCurrentIndex + 1})`);
        if (currentSlide) {
            const slideTitle = currentSlide.querySelector('h3, .promotion-title')?.textContent;
            if (slideTitle) {
                this.announceToScreenReader(`Showing promotion: ${slideTitle}`);
            }
        }
    }
    
    /**
     * Mobile Menu Toggle and Overlay Handling
     * Requirement 7.1: Mobile navigation functionality
     */
    setupMobileMenuHandling() {
        const mobileNavToggle = document.getElementById('mobile-nav-toggle');
        const mobileNavClose = document.getElementById('mobile-nav-close');
        const mobileNav = document.getElementById('mobile-nav');
        const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
        
        if (!mobileNav || !mobileNavOverlay) return;
        
        // Toggle button
        if (mobileNavToggle) {
            mobileNavToggle.addEventListener('click', () => {
                this.openMobileNav();
            });
        }
        
        // Close button
        if (mobileNavClose) {
            mobileNavClose.addEventListener('click', () => {
                this.closeMobileNav();
            });
        }
        
        // Overlay click to close
        mobileNavOverlay.addEventListener('click', () => {
            this.closeMobileNav();
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isMobileNavOpen()) {
                this.closeMobileNav();
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 1024 && this.isMobileNavOpen()) {
                this.closeMobileNav();
            }
        });
    }
    
    openMobileNav() {
        const mobileNav = document.getElementById('mobile-nav');
        const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
        const toggleButton = document.getElementById('mobile-nav-toggle');
        
        if (!mobileNav || !mobileNavOverlay) return;
        
        // Show navigation
        mobileNav.classList.remove('-translate-x-full');
        mobileNavOverlay.classList.remove('hidden');
        
        // Prevent body scroll
        document.body.classList.add('overflow-hidden');
        
        // Update ARIA attributes
        mobileNav.setAttribute('aria-hidden', 'false');
        if (toggleButton) {
            toggleButton.setAttribute('aria-expanded', 'true');
        }
        
        // Focus management
        const firstFocusableElement = mobileNav.querySelector('button, a, input, [tabindex]:not([tabindex="-1"])');
        if (firstFocusableElement) {
            firstFocusableElement.focus();
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Navigation menu opened');
        
        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }
    
    closeMobileNav() {
        const mobileNav = document.getElementById('mobile-nav');
        const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
        const toggleButton = document.getElementById('mobile-nav-toggle');
        
        if (!mobileNav || !mobileNavOverlay) return;
        
        // Hide navigation
        mobileNav.classList.add('-translate-x-full');
        mobileNavOverlay.classList.add('hidden');
        
        // Restore body scroll
        document.body.classList.remove('overflow-hidden');
        
        // Update ARIA attributes
        mobileNav.setAttribute('aria-hidden', 'true');
        if (toggleButton) {
            toggleButton.setAttribute('aria-expanded', 'false');
            toggleButton.focus(); // Return focus to toggle button
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Navigation menu closed');
        
        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }
    
    isMobileNavOpen() {
        const mobileNav = document.getElementById('mobile-nav');
        return mobileNav && !mobileNav.classList.contains('-translate-x-full');
    }
    
    /**
     * Event Listeners and Utility Functions
     */
    setupEventListeners() {
        // Handle window resize for responsive carousel
        window.addEventListener('resize', () => {
            this.updateCarouselPosition();
        });
        
        // Handle visibility change to pause/resume carousel
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseCarouselAutoRotation();
            } else {
                this.startCarouselAutoRotation();
            }
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    // Utility Functions
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
        });
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
    
    announceToScreenReader(message) {
        // Use existing live region or create one
        let liveRegion = document.getElementById('live-region');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        liveRegion.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
    
    triggerRefreshAnimations() {
        // Trigger refresh animations for updated content
        const animatedElements = document.querySelectorAll('.vehicle-overview, .service-info, .cost-analytics');
        
        animatedElements.forEach((element, index) => {
            setTimeout(() => {
                element.classList.add('refresh-animation');
                setTimeout(() => {
                    element.classList.remove('refresh-animation');
                }, 600);
            }, index * 100);
        });
    }
    
    cleanup() {
        this.pauseCarouselAutoRotation();
    }
    
    // Public API
    switchVehicle(vehicleId) {
        const selector = document.querySelector('#vehicle-selector');
        if (selector) {
            selector.value = vehicleId;
            this.handleVehicleSwitch(vehicleId, selector);
        }
    }
    
    goToCarouselSlide(index) {
        this.goToSlide(index);
    }
    
    toggleMobileNav() {
        if (this.isMobileNavOpen()) {
            this.closeMobileNav();
        } else {
            this.openMobileNav();
        }
    }
}

// CSS for animations and screen reader support
const dashboardCoreCSS = `
.refresh-animation {
    animation: refresh-fade 0.6s ease-in-out;
}

@keyframes refresh-fade {
    0% { opacity: 1; transform: translateY(0); }
    50% { opacity: 0.7; transform: translateY(-5px); }
    100% { opacity: 1; transform: translateY(0); }
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* Carousel responsive adjustments */
@media (max-width: 640px) {
    .carousel-slide {
        width: 100% !important;
    }
}

@media (min-width: 641px) and (max-width: 1023px) {
    .carousel-slide {
        width: 50% !important;
    }
}

@media (min-width: 1024px) {
    .carousel-slide {
        width: 33.333333% !important;
    }
}
`;

// Inject CSS
const dashboardCoreStyleSheet = document.createElement('style');
dashboardCoreStyleSheet.textContent = dashboardCoreCSS;
document.head.appendChild(dashboardCoreStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardCore = new DashboardCore();
});

// Export for external use
window.DashboardCore = DashboardCore;