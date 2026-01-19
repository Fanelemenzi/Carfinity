/**
 * Dashboard Hover Interactions and Visual Effects
 * Enhanced interactive animations for the autocare dashboard
 */

class DashboardHoverInteractions {
    constructor() {
        this.isInitialized = false;
        this.animationQueue = [];
        this.observers = new Map();
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupCardHoverEffects();
        this.setupButtonInteractions();
        this.setupLoadingAnimations();
        this.setupShimmerEffects();
        this.setupIconAnimations();
        this.setupProgressBarAnimations();
        this.setupStaggeredAnimations();
        this.setupAccessibilityFeatures();
        
        this.isInitialized = true;
        console.log('Dashboard hover interactions initialized');
    }
    
    setupCardHoverEffects() {
        // Enhanced card hover effects
        const cards = document.querySelectorAll('.dashboard-card, .bg-white.rounded-xl, .promotion-card, .quick-tool-card');
        
        cards.forEach(card => {
            // Add hover class for CSS targeting
            card.classList.add('hover-enhanced');
            
            card.addEventListener('mouseenter', (e) => {
                this.addCardHoverEffect(e.target);
            });
            
            card.addEventListener('mouseleave', (e) => {
                this.removeCardHoverEffect(e.target);
            });
            
            // Add click ripple effect
            card.addEventListener('click', (e) => {
                if (!card.classList.contains('no-ripple')) {
                    this.createRippleEffect(card, e);
                }
            });
        });
        
        // Vehicle overview card special effects
        const vehicleCard = document.querySelector('.vehicle-overview-card, [class*="vehicle"]');
        if (vehicleCard) {
            vehicleCard.addEventListener('mouseenter', () => {
                this.addVehicleCardEffect(vehicleCard);
            });
            
            vehicleCard.addEventListener('mouseleave', () => {
                this.removeVehicleCardEffect(vehicleCard);
            });
        }
    }
    
    setupButtonInteractions() {
        // Enhanced button hover and click effects
        const buttons = document.querySelectorAll('button, .btn, .action-button, a[class*="bg-"]');
        
        buttons.forEach(button => {
            // Add ripple effect class
            button.classList.add('btn-ripple');
            
            button.addEventListener('mouseenter', (e) => {
                this.addButtonHoverEffect(e.target);
            });
            
            button.addEventListener('mouseleave', (e) => {
                this.removeButtonHoverEffect(e.target);
            });
            
            button.addEventListener('mousedown', (e) => {
                this.addButtonPressEffect(e.target);
            });
            
            button.addEventListener('mouseup', (e) => {
                this.removeButtonPressEffect(e.target);
            });
            
            // Add click animation
            button.addEventListener('click', (e) => {
                this.createButtonClickAnimation(button, e);
            });
        });
    }
    
    setupLoadingAnimations() {
        // Setup loading state animations
        const loadingElements = document.querySelectorAll('.loading, .spinner, [class*="loading"]');
        
        loadingElements.forEach(element => {
            this.animateLoadingElement(element);
        });
        
        // Setup skeleton loading
        const skeletonElements = document.querySelectorAll('.skeleton, .loading-skeleton');
        skeletonElements.forEach(skeleton => {
            this.animateSkeletonLoading(skeleton);
        });
    }
    
    setupShimmerEffects() {
        // Add shimmer effects to loading placeholders
        const shimmerElements = document.querySelectorAll('.shimmer, .loading-placeholder');
        
        shimmerElements.forEach(element => {
            element.classList.add('shimmer-loading');
        });
        
        // Create shimmer effect for images while loading
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.complete) {
                this.addImageLoadingShimmer(img);
            }
        });
    }
    
    setupIconAnimations() {
        // Setup icon hover animations
        const icons = document.querySelectorAll('i, .icon, [class*="fa-"]');
        
        icons.forEach(icon => {
            const parent = icon.closest('button, a, .clickable, .nav-item, .tool-card');
            
            if (parent) {
                parent.addEventListener('mouseenter', () => {
                    this.animateIcon(icon, 'bounce');
                });
            }
        });
        
        // Special animations for notification icons
        const notificationIcons = document.querySelectorAll('.fa-bell, .notification-icon');
        notificationIcons.forEach(icon => {
            this.addNotificationIconAnimation(icon);
        });
    }
    
    setupProgressBarAnimations() {
        // Animate progress bars
        const progressBars = document.querySelectorAll('.progress-bar, [class*="progress"]');
        
        progressBars.forEach(bar => {
            this.animateProgressBar(bar);
        });
        
        // Setup health status indicators
        const healthIndicators = document.querySelectorAll('.health-status, .status-bar');
        healthIndicators.forEach(indicator => {
            this.animateHealthIndicator(indicator);
        });
    }
    
    setupStaggeredAnimations() {
        // Setup staggered animations for lists and grids
        const staggerContainers = document.querySelectorAll('.stagger-animation, .grid, .space-y-4');
        
        staggerContainers.forEach(container => {
            this.setupStaggeredContainer(container);
        });
    }
    
    setupAccessibilityFeatures() {
        // Add focus-visible support
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
        
        // Add ARIA live regions for dynamic content
        this.createAriaLiveRegions();
    }
    
    // Animation Methods
    addCardHoverEffect(card) {
        card.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        card.style.transform = 'translateY(-4px)';
        card.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
        
        // Add glow effect for important cards
        if (card.classList.contains('important') || card.classList.contains('vehicle-overview')) {
            card.style.boxShadow += ', 0 0 20px rgba(59, 130, 246, 0.2)';
        }
    }
    
    removeCardHoverEffect(card) {
        card.style.transform = '';
        card.style.boxShadow = '';
    }
    
    addVehicleCardEffect(card) {
        card.style.transform = 'translateY(-6px) scale(1.01)';
        card.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.15)';
        
        // Animate vehicle image if present
        const vehicleImage = card.querySelector('img, .vehicle-image');
        if (vehicleImage) {
            vehicleImage.style.transform = 'scale(1.05)';
        }
    }
    
    removeVehicleCardEffect(card) {
        card.style.transform = '';
        card.style.boxShadow = '';
        
        const vehicleImage = card.querySelector('img, .vehicle-image');
        if (vehicleImage) {
            vehicleImage.style.transform = '';
        }
    }
    
    addButtonHoverEffect(button) {
        button.style.transform = 'translateY(-2px)';
        button.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)';
    }
    
    removeButtonHoverEffect(button) {
        button.style.transform = '';
        button.style.boxShadow = '';
    }
    
    addButtonPressEffect(button) {
        button.style.transform = 'translateY(-1px) scale(0.98)';
    }
    
    removeButtonPressEffect(button) {
        button.style.transform = '';
    }
    
    createRippleEffect(element, event) {
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        const ripple = document.createElement('div');
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(59, 130, 246, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple-expand 0.6s linear;
            pointer-events: none;
            z-index: 1;
        `;
        
        // Ensure element has relative positioning
        const originalPosition = element.style.position;
        if (!originalPosition || originalPosition === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            ripple.remove();
            if (!originalPosition || originalPosition === 'static') {
                element.style.position = originalPosition;
            }
        }, 600);
    }
    
    createButtonClickAnimation(button, event) {
        // Create expanding circle animation
        const rect = button.getBoundingClientRect();
        const circle = document.createElement('div');
        const diameter = Math.max(rect.width, rect.height);
        const radius = diameter / 2;
        
        circle.style.cssText = `
            position: absolute;
            width: ${diameter}px;
            height: ${diameter}px;
            left: ${event.clientX - rect.left - radius}px;
            top: ${event.clientY - rect.top - radius}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: button-click-expand 0.4s ease-out;
            pointer-events: none;
            z-index: 1;
        `;
        
        button.style.position = 'relative';
        button.appendChild(circle);
        
        setTimeout(() => {
            circle.remove();
        }, 400);
    }
    
    animateIcon(icon, animationType) {
        icon.classList.add(`animate-${animationType}`);
        
        setTimeout(() => {
            icon.classList.remove(`animate-${animationType}`);
        }, 600);
    }
    
    addNotificationIconAnimation(icon) {
        // Add pulsing animation for notifications
        icon.classList.add('notification-pulse');
        
        // Add badge bounce if notification badge exists
        const badge = icon.parentElement.querySelector('.notification-badge, .badge');
        if (badge) {
            badge.classList.add('badge-bounce');
        }
    }
    
    animateLoadingElement(element) {
        element.classList.add('pulse-loading');
    }
    
    animateSkeletonLoading(skeleton) {
        skeleton.classList.add('skeleton-card');
    }
    
    addImageLoadingShimmer(img) {
        const placeholder = document.createElement('div');
        placeholder.className = 'shimmer-loading';
        placeholder.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        `;
        
        img.parentElement.style.position = 'relative';
        img.parentElement.appendChild(placeholder);
        
        img.addEventListener('load', () => {
            placeholder.remove();
        });
    }
    
    animateProgressBar(bar) {
        const targetWidth = bar.dataset.width || bar.getAttribute('aria-valuenow') || '0';
        const maxWidth = bar.dataset.max || bar.getAttribute('aria-valuemax') || '100';
        const percentage = (parseInt(targetWidth) / parseInt(maxWidth)) * 100;
        
        bar.style.width = '0%';
        bar.style.transition = 'width 1s cubic-bezier(0.4, 0, 0.2, 1)';
        
        // Animate to target width
        requestAnimationFrame(() => {
            bar.style.width = `${percentage}%`;
        });
        
        // Add shine effect
        bar.classList.add('progress-bar');
    }
    
    animateHealthIndicator(indicator) {
        const healthValue = indicator.dataset.health || '85';
        const healthBar = indicator.querySelector('.health-bar, .progress-bar');
        
        if (healthBar) {
            this.animateProgressBar(healthBar);
        }
        
        // Add color animation based on health value
        const value = parseInt(healthValue);
        let color = '#10b981'; // green
        
        if (value < 30) color = '#ef4444'; // red
        else if (value < 60) color = '#f59e0b'; // yellow
        
        indicator.style.setProperty('--health-color', color);
    }
    
    setupStaggeredContainer(container) {
        const children = Array.from(container.children);
        
        // Add stagger animation class
        container.classList.add('stagger-animation');
        
        // Observe container for intersection
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.triggerStaggeredAnimation(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });
            
            observer.observe(container);
        }
    }
    
    triggerStaggeredAnimation(container) {
        const children = Array.from(container.children);
        
        children.forEach((child, index) => {
            setTimeout(() => {
                child.classList.add('slide-in-animation');
            }, index * 100);
        });
    }
    
    createAriaLiveRegions() {
        // Create live region for announcements
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.id = 'live-region';
        
        document.body.appendChild(liveRegion);
        
        // Store reference for announcements
        this.liveRegion = liveRegion;
    }
    
    // Public API Methods
    announceToScreenReader(message) {
        if (this.liveRegion) {
            this.liveRegion.textContent = message;
            
            // Clear after announcement
            setTimeout(() => {
                this.liveRegion.textContent = '';
            }, 1000);
        }
    }
    
    showLoadingState(element) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay active';
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
        `;
        
        element.style.position = 'relative';
        element.appendChild(overlay);
        
        return overlay;
    }
    
    hideLoadingState(element) {
        const overlay = element.querySelector('.loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }
    
    animateElementIn(element, animationType = 'fade-in') {
        element.classList.add(`${animationType}-animation`);
        
        setTimeout(() => {
            element.classList.remove(`${animationType}-animation`);
        }, 600);
    }
    
    // Cleanup method
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        this.isInitialized = false;
    }
}

// CSS Animations (injected dynamically)
const hoverAnimationCSS = `
@keyframes ripple-expand {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes button-click-expand {
    to {
        transform: scale(2);
        opacity: 0;
    }
}

@keyframes notification-pulse {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}

@keyframes badge-bounce {
    0%, 20%, 53%, 80%, 100% {
        transform: translate3d(0, 0, 0);
    }
    40%, 43% {
        transform: translate3d(0, -4px, 0);
    }
    70% {
        transform: translate3d(0, -2px, 0);
    }
    90% {
        transform: translate3d(0, -1px, 0);
    }
}

.notification-pulse {
    animation: notification-pulse 2s infinite;
}

.badge-bounce {
    animation: badge-bounce 1s ease-in-out infinite;
}

.animate-bounce {
    animation: badge-bounce 0.6s ease-in-out;
}

/* Keyboard navigation styles */
.keyboard-navigation *:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}

/* Screen reader only class */
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
`;

// Inject CSS
const hoverStyleSheet = document.createElement('style');
hoverStyleSheet.textContent = hoverAnimationCSS;
document.head.appendChild(hoverStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardHoverInteractions = new DashboardHoverInteractions();
});

// Export for external use
window.DashboardHoverInteractions = DashboardHoverInteractions;