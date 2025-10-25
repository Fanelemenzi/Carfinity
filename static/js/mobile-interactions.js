/**
 * Mobile Interactions and Touch Gestures for AutoCare Dashboard
 * Implements swipe gestures, pull-to-refresh, and touch-friendly interactions
 */

class MobileInteractions {
    constructor() {
        this.init();
        this.setupTouchGestures();
        this.setupPullToRefresh();
        this.setupMobileNavigation();
    }

    init() {
        // Initialize mobile-specific features
        this.isMobile = window.innerWidth <= 768;
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isRefreshing = false;
        
        // Listen for orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });

        // Listen for resize events
        window.addEventListener('resize', () => {
            this.isMobile = window.innerWidth <= 768;
        });
    }

    setupTouchGestures() {
        // Setup swipe gestures for carousel navigation
        const carousels = document.querySelectorAll('[data-carousel]');
        
        carousels.forEach(carousel => {
            this.setupCarouselSwipe(carousel);
        });

        // Setup swipe gestures for mobile navigation
        this.setupNavigationSwipe();
    }

    setupCarouselSwipe(carousel) {
        let startX = 0;
        let currentX = 0;
        let isDragging = false;

        carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            carousel.style.transition = 'none';
        }, { passive: true });

        carousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            currentX = e.touches[0].clientX;
            const diffX = currentX - startX;
            
            // Add visual feedback during swipe
            carousel.style.transform = `translateX(${diffX}px)`;
        }, { passive: true });

        carousel.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            carousel.style.transition = 'transform 0.3s ease';
            carousel.style.transform = 'translateX(0)';
            
            const diffX = currentX - startX;
            const threshold = 50; // Minimum swipe distance
            
            if (Math.abs(diffX) > threshold) {
                if (diffX > 0) {
                    this.navigateCarousel(carousel, 'prev');
                } else {
                    this.navigateCarousel(carousel, 'next');
                }
            }
        }, { passive: true });
    }

    navigateCarousel(carousel, direction) {
        const items = carousel.querySelectorAll('[data-carousel-item]');
        const currentIndex = parseInt(carousel.dataset.currentIndex || '0');
        let newIndex;

        if (direction === 'next') {
            newIndex = (currentIndex + 1) % items.length;
        } else {
            newIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1;
        }

        // Update carousel position
        carousel.dataset.currentIndex = newIndex;
        this.updateCarouselPosition(carousel, newIndex);
        
        // Trigger haptic feedback if available
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }

    updateCarouselPosition(carousel, index) {
        const items = carousel.querySelectorAll('[data-carousel-item]');
        const itemWidth = items[0].offsetWidth;
        const offset = -index * itemWidth;
        
        carousel.style.transform = `translateX(${offset}px)`;
        
        // Update indicators if they exist
        const indicators = carousel.parentElement.querySelectorAll('[data-carousel-indicator]');
        indicators.forEach((indicator, i) => {
            indicator.classList.toggle('active', i === index);
        });
    }

    setupNavigationSwipe() {
        const mobileNav = document.getElementById('mobile-nav');
        const overlay = document.getElementById('mobile-nav-overlay');
        
        if (!mobileNav || !overlay) return;

        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        let navWidth = mobileNav.offsetWidth;

        // Swipe to open navigation from left edge
        document.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            if (touch.clientX < 20 && !mobileNav.classList.contains('translate-x-0')) {
                startX = touch.clientX;
                isDragging = true;
            }
        }, { passive: true });

        // Swipe to close navigation when open
        mobileNav.addEventListener('touchstart', (e) => {
            if (mobileNav.classList.contains('translate-x-0')) {
                startX = e.touches[0].clientX;
                isDragging = true;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            currentX = e.touches[0].clientX;
            const diffX = currentX - startX;
            
            // Only allow swipe in appropriate direction
            if (mobileNav.classList.contains('translate-x-0')) {
                // Navigation is open, allow swipe left to close
                if (diffX < 0) {
                    const progress = Math.max(0, 1 + diffX / navWidth);
                    mobileNav.style.transform = `translateX(${diffX}px)`;
                    overlay.style.opacity = progress * 0.5;
                }
            } else {
                // Navigation is closed, allow swipe right to open
                if (diffX > 0) {
                    const progress = Math.min(1, diffX / navWidth);
                    mobileNav.style.transform = `translateX(${-navWidth + diffX}px)`;
                    overlay.style.opacity = progress * 0.5;
                    overlay.classList.remove('hidden');
                }
            }
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            const diffX = currentX - startX;
            const threshold = navWidth * 0.3; // 30% of nav width
            
            mobileNav.style.transform = '';
            overlay.style.opacity = '';
            
            if (mobileNav.classList.contains('translate-x-0')) {
                // Navigation is open
                if (diffX < -threshold) {
                    this.closeMobileNav();
                }
            } else {
                // Navigation is closed
                if (diffX > threshold) {
                    this.openMobileNav();
                } else {
                    overlay.classList.add('hidden');
                }
            }
        }, { passive: true });
    }

    setupPullToRefresh() {
        const mainContent = document.querySelector('main');
        if (!mainContent) return;

        let startY = 0;
        let currentY = 0;
        let isDragging = false;
        let refreshThreshold = 80;
        
        // Create pull-to-refresh indicator
        const refreshIndicator = document.createElement('div');
        refreshIndicator.id = 'pull-refresh-indicator';
        refreshIndicator.className = 'fixed top-0 left-0 right-0 bg-indigo-600 text-white text-center py-2 transform -translate-y-full transition-transform duration-300 z-50';
        refreshIndicator.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <i class="fas fa-sync-alt text-sm"></i>
                <span class="text-sm font-medium">Pull to refresh</span>
            </div>
        `;
        document.body.appendChild(refreshIndicator);

        mainContent.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isDragging = true;
            }
        }, { passive: true });

        mainContent.addEventListener('touchmove', (e) => {
            if (!isDragging || window.scrollY > 0) return;
            
            currentY = e.touches[0].clientY;
            const diffY = currentY - startY;
            
            if (diffY > 0) {
                e.preventDefault();
                const progress = Math.min(1, diffY / refreshThreshold);
                const translateY = Math.min(diffY * 0.5, refreshThreshold * 0.5);
                
                refreshIndicator.style.transform = `translateY(${translateY - refreshIndicator.offsetHeight}px)`;
                
                if (progress >= 1) {
                    refreshIndicator.innerHTML = `
                        <div class="flex items-center justify-center space-x-2">
                            <i class="fas fa-arrow-up text-sm"></i>
                            <span class="text-sm font-medium">Release to refresh</span>
                        </div>
                    `;
                } else {
                    refreshIndicator.innerHTML = `
                        <div class="flex items-center justify-center space-x-2">
                            <i class="fas fa-sync-alt text-sm"></i>
                            <span class="text-sm font-medium">Pull to refresh</span>
                        </div>
                    `;
                }
            }
        });

        mainContent.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            isDragging = false;
            const diffY = currentY - startY;
            
            refreshIndicator.style.transform = 'translateY(-100%)';
            
            if (diffY > refreshThreshold && !this.isRefreshing) {
                this.triggerRefresh();
            }
        }, { passive: true });
    }

    triggerRefresh() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        const refreshIndicator = document.getElementById('pull-refresh-indicator');
        
        refreshIndicator.style.transform = 'translateY(0)';
        refreshIndicator.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <i class="fas fa-spinner fa-spin text-sm"></i>
                <span class="text-sm font-medium">Refreshing...</span>
            </div>
        `;
        
        // Trigger haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate([50, 50, 50]);
        }
        
        // Simulate refresh (replace with actual refresh logic)
        setTimeout(() => {
            this.completeRefresh();
        }, 2000);
    }

    completeRefresh() {
        this.isRefreshing = false;
        const refreshIndicator = document.getElementById('pull-refresh-indicator');
        
        refreshIndicator.innerHTML = `
            <div class="flex items-center justify-center space-x-2">
                <i class="fas fa-check text-sm"></i>
                <span class="text-sm font-medium">Refreshed</span>
            </div>
        `;
        
        setTimeout(() => {
            refreshIndicator.style.transform = 'translateY(-100%)';
            setTimeout(() => {
                refreshIndicator.innerHTML = `
                    <div class="flex items-center justify-center space-x-2">
                        <i class="fas fa-sync-alt text-sm"></i>
                        <span class="text-sm font-medium">Pull to refresh</span>
                    </div>
                `;
            }, 300);
        }, 1000);
        
        // Reload page or refresh data
        window.location.reload();
    }

    setupMobileNavigation() {
        const mobileNavToggle = document.getElementById('mobile-nav-toggle');
        const mobileNavClose = document.getElementById('mobile-nav-close');
        const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
        
        if (mobileNavToggle) {
            mobileNavToggle.addEventListener('click', () => this.openMobileNav());
        }
        
        if (mobileNavClose) {
            mobileNavClose.addEventListener('click', () => this.closeMobileNav());
        }
        
        if (mobileNavOverlay) {
            mobileNavOverlay.addEventListener('click', () => this.closeMobileNav());
        }
    }

    openMobileNav() {
        const mobileNav = document.getElementById('mobile-nav');
        const overlay = document.getElementById('mobile-nav-overlay');
        
        if (mobileNav && overlay) {
            mobileNav.classList.remove('-translate-x-full');
            mobileNav.classList.add('translate-x-0');
            overlay.classList.remove('hidden');
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
            
            // Trigger haptic feedback
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }

    closeMobileNav() {
        const mobileNav = document.getElementById('mobile-nav');
        const overlay = document.getElementById('mobile-nav-overlay');
        
        if (mobileNav && overlay) {
            mobileNav.classList.remove('translate-x-0');
            mobileNav.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
            
            // Restore body scroll
            document.body.style.overflow = '';
            
            // Trigger haptic feedback
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }

    handleOrientationChange() {
        // Handle orientation changes
        const mobileNav = document.getElementById('mobile-nav');
        if (mobileNav && mobileNav.classList.contains('translate-x-0')) {
            // Close navigation on orientation change
            this.closeMobileNav();
        }
        
        // Recalculate dimensions
        setTimeout(() => {
            this.init();
        }, 500);
    }
}

// Initialize mobile interactions when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MobileInteractions();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileInteractions;
}