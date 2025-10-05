/**
 * Dashboard Animations and Micro-interactions
 * Handles smooth animations and visual feedback across all dashboard pages
 */

class DashboardAnimations {
    constructor() {
        this.animationQueue = [];
        this.isAnimating = false;
        this.observers = new Map();
        
        this.init();
    }
    
    init() {
        this.setupIntersectionObserver();
        this.setupHoverAnimations();
        this.setupClickAnimations();
        this.setupLoadingAnimations();
        this.setupScrollAnimations();
        this.setupFormAnimations();
    }
    
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            // Fade in animation observer
            const fadeInObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.animateElement(entry.target, 'fadeIn');
                        fadeInObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });
            
            // Slide in animation observer
            const slideInObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const direction = entry.target.dataset.slideDirection || 'up';
                        this.animateElement(entry.target, `slideIn${direction.charAt(0).toUpperCase() + direction.slice(1)}`);
                        slideInObserver.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '50px'
            });
            
            // Observe elements with animation classes
            document.querySelectorAll('[data-animate="fade"]').forEach(el => {
                fadeInObserver.observe(el);
            });
            
            document.querySelectorAll('[data-animate="slide"]').forEach(el => {
                slideInObserver.observe(el);
            });
            
            this.observers.set('fadeIn', fadeInObserver);
            this.observers.set('slideIn', slideInObserver);
        }
    }
    
    setupHoverAnimations() {
        // Card hover effects
        const cards = document.querySelectorAll('.dashboard-card, .action-card, .kpi-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.addHoverEffect(card);
            });
            
            card.addEventListener('mouseleave', () => {
                this.removeHoverEffect(card);
            });
        });
        
        // Button hover effects
        const buttons = document.querySelectorAll('.action-button, .nav-item');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', () => {
                this.addButtonHover(button);
            });
            
            button.addEventListener('mouseleave', () => {
                this.removeButtonHover(button);
            });
        });
        
        // Icon hover effects
        const icons = document.querySelectorAll('.hover-icon');
        icons.forEach(icon => {
            icon.addEventListener('mouseenter', () => {
                this.animateIcon(icon, 'bounce');
            });
        });
    }
    
    setupClickAnimations() {
        // Click ripple effect
        document.addEventListener('click', (e) => {
            const clickableElements = [
                '.action-button',
                '.dashboard-card',
                '.kpi-card',
                '.nav-item',
                'button'
            ];
            
            const element = e.target.closest(clickableElements.join(', '));
            if (element && !element.classList.contains('no-ripple')) {
                this.createRippleEffect(element, e);
            }
        });
        
        // Scale animation on click
        const scaleElements = document.querySelectorAll('.click-scale');
        scaleElements.forEach(element => {
            element.addEventListener('mousedown', () => {
                element.style.transform = 'scale(0.98)';
            });
            
            element.addEventListener('mouseup', () => {
                element.style.transform = '';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = '';
            });
        });
    }
    
    setupLoadingAnimations() {
        // Skeleton loading animation
        const skeletons = document.querySelectorAll('.loading-skeleton');
        skeletons.forEach(skeleton => {
            this.animateSkeleton(skeleton);
        });
        
        // Progress bar animations
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            this.animateProgressBar(bar);
        });
        
        // Spinner animations
        const spinners = document.querySelectorAll('.loading-spinner');
        spinners.forEach(spinner => {
            this.animateSpinner(spinner);
        });
    }
    
    setupScrollAnimations() {
        // Parallax effect for hero sections
        const parallaxElements = document.querySelectorAll('[data-parallax]');
        
        if (parallaxElements.length > 0) {
            window.addEventListener('scroll', this.throttle(() => {
                this.updateParallax(parallaxElements);
            }, 16));
        }
        
        // Sticky header animation
        const header = document.querySelector('.dashboard-header');
        if (header) {
            window.addEventListener('scroll', this.throttle(() => {
                this.updateStickyHeader(header);
            }, 16));
        }
    }
    
    setupFormAnimations() {
        // Input focus animations
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                this.animateInputFocus(input);
            });
            
            input.addEventListener('blur', () => {
                this.animateInputBlur(input);
            });
        });
        
        // Form validation animations
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    this.animateFormErrors(form);
                }
            });
        });
    }
    
    // Animation methods
    animateElement(element, animationType, options = {}) {
        const defaultOptions = {
            duration: 600,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
            delay: 0
        };
        
        const config = { ...defaultOptions, ...options };
        
        element.style.animationDuration = `${config.duration}ms`;
        element.style.animationTimingFunction = config.easing;
        element.style.animationDelay = `${config.delay}ms`;
        
        element.classList.add(animationType);
        
        // Clean up after animation
        setTimeout(() => {
            element.classList.remove(animationType);
            element.style.animationDuration = '';
            element.style.animationTimingFunction = '';
            element.style.animationDelay = '';
        }, config.duration + config.delay);
    }
    
    addHoverEffect(element) {
        element.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        element.style.transform = 'translateY(-4px)';
        element.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
    }
    
    removeHoverEffect(element) {
        element.style.transform = '';
        element.style.boxShadow = '';
    }
    
    addButtonHover(button) {
        button.style.transition = 'all 0.2s ease';
        button.style.transform = 'translateY(-1px)';
    }
    
    removeButtonHover(button) {
        button.style.transform = '';
    }
    
    animateIcon(icon, animationType) {
        icon.classList.add(`animate-${animationType}`);
        setTimeout(() => {
            icon.classList.remove(`animate-${animationType}`);
        }, 600);
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
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
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
    
    animateSkeleton(skeleton) {
        skeleton.style.background = 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)';
        skeleton.style.backgroundSize = '200% 100%';
        skeleton.style.animation = 'skeleton-loading 1.5s infinite';
    }
    
    animateProgressBar(bar) {
        const targetWidth = bar.dataset.width || bar.style.width || '0%';
        bar.style.width = '0%';
        bar.style.transition = 'width 1s cubic-bezier(0.4, 0, 0.2, 1)';
        
        // Animate to target width
        requestAnimationFrame(() => {
            bar.style.width = targetWidth;
        });
    }
    
    animateSpinner(spinner) {
        spinner.style.animation = 'spin 1s linear infinite';
    }
    
    updateParallax(elements) {
        const scrollY = window.pageYOffset;
        
        elements.forEach(element => {
            const speed = parseFloat(element.dataset.parallax) || 0.5;
            const yPos = -(scrollY * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    }
    
    updateStickyHeader(header) {
        const scrollY = window.pageYOffset;
        
        if (scrollY > 100) {
            header.classList.add('scrolled');
            header.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
        } else {
            header.classList.remove('scrolled');
            header.style.boxShadow = '';
        }
    }
    
    animateInputFocus(input) {
        const parent = input.parentElement;
        parent.classList.add('input-focused');
        
        // Create focus ring animation
        input.style.transition = 'all 0.2s ease';
        input.style.boxShadow = '0 0 0 2px rgba(59, 130, 246, 0.5)';
    }
    
    animateInputBlur(input) {
        const parent = input.parentElement;
        parent.classList.remove('input-focused');
        input.style.boxShadow = '';
    }
    
    animateFormErrors(form) {
        const invalidInputs = form.querySelectorAll(':invalid');
        
        invalidInputs.forEach((input, index) => {
            setTimeout(() => {
                this.shakeElement(input);
            }, index * 100);
        });
    }
    
    shakeElement(element) {
        element.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }
    
    // Utility methods
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Public API methods
    fadeIn(element, options = {}) {
        this.animateElement(element, 'fade-in', options);
    }
    
    slideIn(element, direction = 'up', options = {}) {
        const animationClass = `slide-in-${direction}`;
        this.animateElement(element, animationClass, options);
    }
    
    bounceIn(element, options = {}) {
        this.animateElement(element, 'bounce-in', options);
    }
    
    pulse(element, options = {}) {
        this.animateElement(element, 'pulse', options);
    }
    
    // Staggered animations
    staggeredAnimation(elements, animationType, staggerDelay = 100) {
        elements.forEach((element, index) => {
            setTimeout(() => {
                this.animateElement(element, animationType);
            }, index * staggerDelay);
        });
    }
    
    // Page transition animations
    pageTransitionOut(callback) {
        const main = document.querySelector('main, .main-content');
        if (main) {
            main.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            main.style.opacity = '0';
            main.style.transform = 'translateY(20px)';
            
            setTimeout(callback, 300);
        } else {
            callback();
        }
    }
    
    pageTransitionIn() {
        const main = document.querySelector('main, .main-content');
        if (main) {
            main.style.opacity = '0';
            main.style.transform = 'translateY(20px)';
            
            requestAnimationFrame(() => {
                main.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                main.style.opacity = '1';
                main.style.transform = 'translateY(0)';
            });
        }
    }
    
    // Cleanup method
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
    }
}

// CSS animations (injected dynamically)
const animationCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes skeleton-loading {
    0% {
        background-position: 200% 0;
    }
    100% {
        background-position: -200% 0;
    }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

@keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0,-8px,0); }
    70% { transform: translate3d(0,-4px,0); }
    90% { transform: translate3d(0,-2px,0); }
}

.animate-bounce { animation: bounce 1s ease-in-out; }
.animate-pulse { animation: pulse 2s infinite; }
.animate-shake { animation: shake 0.5s ease-in-out; }

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
`;

// Inject CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = animationCSS;
document.head.appendChild(styleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardAnimations = new DashboardAnimations();
});

// Export for external use
window.DashboardAnimations = DashboardAnimations;