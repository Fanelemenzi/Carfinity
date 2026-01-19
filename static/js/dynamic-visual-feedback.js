/**
 * Dynamic Visual Feedback System
 * Handles button click animations, notification badges, and page transitions
 */

class DynamicVisualFeedback {
    constructor() {
        this.isInitialized = false;
        this.activeAnimations = new Set();
        this.notificationQueue = [];
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupButtonClickAnimations();
        this.setupNotificationBadgeAnimations();
        this.setupPageTransitionEffects();
        this.setupFormFeedback();
        this.setupLoadingStates();
        this.setupSuccessAnimations();
        this.setupErrorAnimations();
        
        this.isInitialized = true;
        console.log('Dynamic visual feedback system initialized');
    }
    
    setupButtonClickAnimations() {
        // Enhanced button click animations with state changes
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn, .action-button, a[role="button"]');
            
            if (button && !button.disabled) {
                this.createButtonClickFeedback(button, e);
                this.addButtonStateAnimation(button);
            }
        });
        
        // Special handling for form submit buttons
        document.addEventListener('submit', (e) => {
            const submitButton = e.target.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton) {
                this.createSubmitButtonAnimation(submitButton);
            }
        });
    }
    
    setupNotificationBadgeAnimations() {
        // Animate notification badges with bounce and pulse effects
        const badges = document.querySelectorAll('.notification-badge, .badge, [class*="badge"]');
        
        badges.forEach(badge => {
            this.animateNotificationBadge(badge);
        });
        
        // Setup notification bell animations
        const notificationBells = document.querySelectorAll('.fa-bell, .notification-icon');
        notificationBells.forEach(bell => {
            this.setupNotificationBellAnimation(bell);
        });
        
        // Setup dynamic badge updates
        this.setupDynamicBadgeUpdates();
    }
    
    setupPageTransitionEffects() {
        // Setup page transition animations for navigation
        const navLinks = document.querySelectorAll('a[href]:not([href^="#"]):not([href^="javascript:"]):not([target="_blank"])');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
                    this.createPageTransitionOut(() => {
                        window.location.href = link.href;
                    });
                    e.preventDefault();
                }
            });
        });
        
        // Setup page transition in on load
        this.createPageTransitionIn();
    }
    
    setupFormFeedback() {
        // Setup form validation feedback animations
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                input.addEventListener('invalid', (e) => {
                    this.createInputErrorAnimation(e.target);
                });
                
                input.addEventListener('input', (e) => {
                    if (e.target.checkValidity()) {
                        this.createInputSuccessAnimation(e.target);
                    }
                });
            });
        });
    }
    
    setupLoadingStates() {
        // Setup loading state animations for AJAX requests
        this.setupAjaxLoadingStates();
        
        // Setup button loading states
        this.setupButtonLoadingStates();
    }
    
    setupSuccessAnimations() {
        // Setup success feedback animations
        this.createSuccessAnimationSystem();
    }
    
    setupErrorAnimations() {
        // Setup error feedback animations
        this.createErrorAnimationSystem();
    }
    
    // Button Click Animation Methods
    createButtonClickFeedback(button, event) {
        // Create ripple effect
        this.createAdvancedRipple(button, event);
        
        // Add click scale animation
        this.addClickScaleAnimation(button);
        
        // Add button press feedback
        this.addButtonPressEffect(button);
    }
    
    createAdvancedRipple(button, event) {
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 2;
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        const ripple = document.createElement('div');
        ripple.className = 'advanced-ripple';
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: radial-gradient(circle, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.1) 70%, transparent 100%);
            border-radius: 50%;
            transform: scale(0);
            animation: advanced-ripple 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            z-index: 1;
        `;
        
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 800);
    }
    
    addClickScaleAnimation(button) {
        button.style.transform = 'scale(0.95)';
        button.style.transition = 'transform 0.1s ease';
        
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }
    
    addButtonPressEffect(button) {
        button.classList.add('button-pressed');
        
        setTimeout(() => {
            button.classList.remove('button-pressed');
        }, 200);
    }
    
    addButtonStateAnimation(button) {
        // Add visual state change animation
        const originalBg = button.style.backgroundColor;
        const originalTransform = button.style.transform;
        
        button.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
        button.style.transform = 'translateY(1px)';
        
        setTimeout(() => {
            button.style.transform = originalTransform;
        }, 100);
    }
    
    createSubmitButtonAnimation(button) {
        // Special animation for submit buttons
        button.classList.add('submitting');
        
        const originalText = button.textContent;
        const spinner = document.createElement('i');
        spinner.className = 'fas fa-spinner fa-spin mr-2';
        
        button.innerHTML = '';
        button.appendChild(spinner);
        button.appendChild(document.createTextNode('Processing...'));
        
        // This would be removed by the form handler on completion
        button.dataset.originalText = originalText;
    }
    
    // Notification Badge Animation Methods
    animateNotificationBadge(badge) {
        // Add entrance animation
        badge.classList.add('badge-entrance');
        
        // Add periodic pulse animation
        setInterval(() => {
            if (badge.isConnected) {
                badge.classList.add('badge-pulse');
                setTimeout(() => {
                    badge.classList.remove('badge-pulse');
                }, 1000);
            }
        }, 5000);
    }
    
    setupNotificationBellAnimation(bell) {
        const badge = bell.parentElement.querySelector('.notification-badge, .badge');
        
        if (badge) {
            // Add shake animation when new notification arrives
            bell.addEventListener('notification-update', () => {
                this.createBellShakeAnimation(bell);
            });
        }
    }
    
    createBellShakeAnimation(bell) {
        bell.classList.add('bell-shake');
        
        setTimeout(() => {
            bell.classList.remove('bell-shake');
        }, 600);
    }
    
    setupDynamicBadgeUpdates() {
        // Setup system for dynamic badge updates
        window.updateNotificationBadge = (element, count) => {
            const badge = element.querySelector('.notification-badge, .badge');
            
            if (badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.classList.add('badge-update');
                    
                    setTimeout(() => {
                        badge.classList.remove('badge-update');
                    }, 500);
                } else {
                    badge.classList.add('badge-fadeout');
                    setTimeout(() => {
                        badge.style.display = 'none';
                    }, 300);
                }
            }
        };
    }
    
    // Page Transition Methods
    createPageTransitionOut(callback) {
        const main = document.querySelector('main, .main-content, #main-content');
        
        if (main) {
            main.classList.add('page-transition-out');
            
            setTimeout(() => {
                if (callback) callback();
            }, 300);
        } else {
            if (callback) callback();
        }
    }
    
    createPageTransitionIn() {
        const main = document.querySelector('main, .main-content, #main-content');
        
        if (main) {
            main.classList.add('page-transition-in');
            
            setTimeout(() => {
                main.classList.remove('page-transition-in');
            }, 600);
        }
    }
    
    // Form Feedback Methods
    createInputErrorAnimation(input) {
        input.classList.add('input-error-shake');
        
        // Add error styling
        input.style.borderColor = '#ef4444';
        input.style.boxShadow = '0 0 0 1px #ef4444';
        
        setTimeout(() => {
            input.classList.remove('input-error-shake');
        }, 500);
    }
    
    createInputSuccessAnimation(input) {
        input.classList.add('input-success-glow');
        
        // Add success styling
        input.style.borderColor = '#10b981';
        input.style.boxShadow = '0 0 0 1px #10b981';
        
        setTimeout(() => {
            input.classList.remove('input-success-glow');
            input.style.borderColor = '';
            input.style.boxShadow = '';
        }, 1000);
    }
    
    // AJAX Loading States
    setupAjaxLoadingStates() {
        // Intercept fetch requests to show loading states
        const originalFetch = window.fetch;
        
        window.fetch = (...args) => {
            this.showGlobalLoadingState();
            
            return originalFetch(...args)
                .then(response => {
                    this.hideGlobalLoadingState();
                    return response;
                })
                .catch(error => {
                    this.hideGlobalLoadingState();
                    this.showErrorFeedback('Network error occurred');
                    throw error;
                });
        };
    }
    
    setupButtonLoadingStates() {
        // Setup loading states for buttons
        window.setButtonLoading = (button, loading = true) => {
            if (loading) {
                button.classList.add('button-loading');
                button.disabled = true;
                
                const originalText = button.textContent;
                button.dataset.originalText = originalText;
                
                const spinner = document.createElement('i');
                spinner.className = 'fas fa-spinner fa-spin mr-2';
                
                button.innerHTML = '';
                button.appendChild(spinner);
                button.appendChild(document.createTextNode('Loading...'));
            } else {
                button.classList.remove('button-loading');
                button.disabled = false;
                
                const originalText = button.dataset.originalText || 'Submit';
                button.textContent = originalText;
                delete button.dataset.originalText;
            }
        };
    }
    
    // Success Animation System
    createSuccessAnimationSystem() {
        window.showSuccessFeedback = (message, element = null) => {
            this.createSuccessToast(message);
            
            if (element) {
                this.addSuccessGlow(element);
            }
        };
    }
    
    createSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-check-circle text-green-500 text-xl"></i>
                <span class="text-gray-900 font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('toast-show');
        }, 100);
        
        // Animate out
        setTimeout(() => {
            toast.classList.add('toast-hide');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
    
    addSuccessGlow(element) {
        element.classList.add('success-glow');
        
        setTimeout(() => {
            element.classList.remove('success-glow');
        }, 2000);
    }
    
    // Error Animation System
    createErrorAnimationSystem() {
        window.showErrorFeedback = (message, element = null) => {
            this.createErrorToast(message);
            
            if (element) {
                this.addErrorShake(element);
            }
        };
    }
    
    createErrorToast(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-exclamation-circle text-red-500 text-xl"></i>
                <span class="text-gray-900 font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('toast-show');
        }, 100);
        
        // Animate out
        setTimeout(() => {
            toast.classList.add('toast-hide');
            setTimeout(() => {
                toast.remove();
            }, 4000);
        }, 4000);
    }
    
    addErrorShake(element) {
        element.classList.add('error-shake');
        
        setTimeout(() => {
            element.classList.remove('error-shake');
        }, 600);
    }
    
    // Global Loading State
    showGlobalLoadingState() {
        let loader = document.getElementById('global-loader');
        
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'global-loader';
            loader.className = 'global-loader';
            loader.innerHTML = `
                <div class="loader-content">
                    <div class="loader-spinner"></div>
                    <span class="loader-text">Loading...</span>
                </div>
            `;
            document.body.appendChild(loader);
        }
        
        loader.classList.add('loader-show');
    }
    
    hideGlobalLoadingState() {
        const loader = document.getElementById('global-loader');
        
        if (loader) {
            loader.classList.remove('loader-show');
        }
    }
    
    // Public API Methods
    triggerSuccessAnimation(element) {
        element.classList.add('success-pulse');
        
        setTimeout(() => {
            element.classList.remove('success-pulse');
        }, 1000);
    }
    
    triggerErrorAnimation(element) {
        element.classList.add('error-shake');
        
        setTimeout(() => {
            element.classList.remove('error-shake');
        }, 600);
    }
    
    animateCounter(element, start, end, duration = 1000) {
        const startTime = performance.now();
        
        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };
        
        requestAnimationFrame(updateCounter);
    }
    
    // Cleanup method
    destroy() {
        this.activeAnimations.clear();
        this.notificationQueue = [];
        this.isInitialized = false;
    }
}

// CSS Animations for Dynamic Visual Feedback
const dynamicFeedbackCSS = `
/* Advanced Ripple Effect */
@keyframes advanced-ripple {
    0% {
        transform: scale(0);
        opacity: 1;
    }
    100% {
        transform: scale(1);
        opacity: 0;
    }
}

/* Button Press Effect */
.button-pressed {
    transform: scale(0.95) !important;
    filter: brightness(0.9);
}

/* Badge Animations */
.badge-entrance {
    animation: badge-entrance 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes badge-entrance {
    0% {
        transform: scale(0);
        opacity: 0;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

.badge-pulse {
    animation: badge-pulse 1s ease-in-out;
}

@keyframes badge-pulse {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.2);
    }
}

.badge-update {
    animation: badge-update 0.5s ease-out;
}

@keyframes badge-update {
    0% {
        transform: scale(1);
        background-color: currentColor;
    }
    50% {
        transform: scale(1.3);
        background-color: #f59e0b;
    }
    100% {
        transform: scale(1);
        background-color: currentColor;
    }
}

.badge-fadeout {
    animation: badge-fadeout 0.3s ease-out forwards;
}

@keyframes badge-fadeout {
    0% {
        opacity: 1;
        transform: scale(1);
    }
    100% {
        opacity: 0;
        transform: scale(0);
    }
}

/* Bell Shake Animation */
.bell-shake {
    animation: bell-shake 0.6s ease-in-out;
}

@keyframes bell-shake {
    0%, 100% { transform: rotate(0deg); }
    10%, 30%, 50%, 70%, 90% { transform: rotate(-10deg); }
    20%, 40%, 60%, 80% { transform: rotate(10deg); }
}

/* Page Transitions */
.page-transition-out {
    animation: page-transition-out 0.3s ease-in forwards;
}

@keyframes page-transition-out {
    0% {
        opacity: 1;
        transform: translateY(0);
    }
    100% {
        opacity: 0;
        transform: translateY(-20px);
    }
}

.page-transition-in {
    animation: page-transition-in 0.6s ease-out;
}

@keyframes page-transition-in {
    0% {
        opacity: 0;
        transform: translateY(20px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Input Animations */
.input-error-shake {
    animation: input-error-shake 0.5s ease-in-out;
}

@keyframes input-error-shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.input-success-glow {
    animation: input-success-glow 1s ease-out;
}

@keyframes input-success-glow {
    0% {
        box-shadow: 0 0 0 1px #10b981;
    }
    50% {
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3);
    }
    100% {
        box-shadow: 0 0 0 1px #10b981;
    }
}

/* Success Animations */
.success-glow {
    animation: success-glow 2s ease-out;
}

@keyframes success-glow {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
    50% {
        box-shadow: 0 0 20px 5px rgba(16, 185, 129, 0.3);
    }
}

.success-pulse {
    animation: success-pulse 1s ease-out;
}

@keyframes success-pulse {
    0%, 100% {
        transform: scale(1);
        background-color: currentColor;
    }
    50% {
        transform: scale(1.05);
        background-color: #10b981;
    }
}

/* Error Animations */
.error-shake {
    animation: error-shake 0.6s ease-in-out;
}

@keyframes error-shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
    20%, 40%, 60%, 80% { transform: translateX(8px); }
}

/* Toast Notifications */
.success-toast,
.error-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 0.75rem;
    padding: 1rem 1.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    border-left: 4px solid #10b981;
    z-index: 1000;
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.error-toast {
    border-left-color: #ef4444;
}

.toast-show {
    transform: translateX(0);
    opacity: 1;
}

.toast-hide {
    transform: translateX(100%);
    opacity: 0;
}

/* Global Loader */
.global-loader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.loader-show {
    opacity: 1;
    visibility: visible;
}

.loader-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    space-y: 1rem;
}

.loader-spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid #e5e7eb;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.loader-text {
    color: #6b7280;
    font-weight: 500;
    margin-top: 1rem;
}

/* Button Loading State */
.button-loading {
    opacity: 0.7;
    cursor: not-allowed;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
    .badge-entrance,
    .badge-pulse,
    .badge-update,
    .bell-shake,
    .page-transition-out,
    .page-transition-in,
    .input-error-shake,
    .input-success-glow,
    .success-glow,
    .success-pulse,
    .error-shake {
        animation: none !important;
    }
    
    .success-toast,
    .error-toast,
    .global-loader {
        transition: none !important;
    }
}
`;

// Inject CSS
const dynamicFeedbackStyleSheet = document.createElement('style');
dynamicFeedbackStyleSheet.textContent = dynamicFeedbackCSS;
document.head.appendChild(dynamicFeedbackStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dynamicVisualFeedback = new DynamicVisualFeedback();
});

// Export for external use
window.DynamicVisualFeedback = DynamicVisualFeedback;