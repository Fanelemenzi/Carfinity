/**
 * Performance Optimization System for AutoCare Dashboard
 * Implements critical CSS inlining, lazy loading, loading states, error handling, and image optimization
 */

class PerformanceOptimization {
    constructor() {
        this.isInitialized = false;
        this.loadingStates = new Map();
        this.imageObserver = null;
        this.contentObserver = null;
        this.criticalResources = [];
        this.deferredResources = [];
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.setupCriticalResourceLoading();
        this.setupLazyLoading();
        this.setupImageOptimization();
        this.setupLoadingStates();
        this.setupErrorHandling();
        this.setupResourcePreloading();
        this.setupPerformanceMonitoring();
        this.setupCacheOptimization();
        
        this.isInitialized = true;
        console.log('Performance optimization system initialized');
    }
    
    setupCriticalResourceLoading() {
        // Inline critical CSS for above-the-fold content
        this.inlineCriticalCSS();
        
        // Defer non-critical CSS
        this.deferNonCriticalCSS();
        
        // Optimize JavaScript loading
        this.optimizeJavaScriptLoading();
        
        // Preload critical resources
        this.preloadCriticalResources();
    }
    
    inlineCriticalCSS() {
        // Critical CSS for above-the-fold content
        const criticalCSS = `
            /* Critical CSS for initial render */
            .min-h-screen { min-height: 100vh; }
            .bg-gray-50 { background-color: #f9fafb; }
            .bg-white { background-color: #ffffff; }
            .shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
            .border-b { border-bottom-width: 1px; }
            .border-gray-200 { border-color: #e5e7eb; }
            .sticky { position: sticky; }
            .top-0 { top: 0; }
            .z-30 { z-index: 30; }
            .flex { display: flex; }
            .items-center { align-items: center; }
            .justify-between { justify-content: space-between; }
            .h-16 { height: 4rem; }
            .max-w-7xl { max-width: 80rem; }
            .mx-auto { margin-left: auto; margin-right: auto; }
            .px-4 { padding-left: 1rem; padding-right: 1rem; }
            .py-4 { padding-top: 1rem; padding-bottom: 1rem; }
            .text-xl { font-size: 1.25rem; line-height: 1.75rem; }
            .font-bold { font-weight: 700; }
            .text-gray-900 { color: #111827; }
            .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
            .text-gray-500 { color: #6b7280; }
            .hidden { display: none; }
            .lg\\:hidden { display: none; }
            @media (min-width: 1024px) {
                .lg\\:hidden { display: none; }
                .lg\\:flex { display: flex; }
            }
            @media (min-width: 640px) {
                .sm\\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
                .sm\\:py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
                .sm\\:block { display: block; }
            }
            /* Loading skeleton styles */
            .skeleton {
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
            }
            @keyframes loading {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }
        `;
        
        // Create and inject critical CSS
        const criticalStyle = document.createElement('style');
        criticalStyle.textContent = criticalCSS;
        criticalStyle.setAttribute('data-critical', 'true');
        document.head.insertBefore(criticalStyle, document.head.firstChild);
    }
    
    deferNonCriticalCSS() {
        // Defer non-critical stylesheets
        const nonCriticalStyles = document.querySelectorAll('link[rel="stylesheet"]:not([data-critical])');
        
        nonCriticalStyles.forEach(link => {
            // Skip if already processed
            if (link.hasAttribute('data-deferred')) return;
            
            const href = link.href;
            link.setAttribute('data-deferred', 'true');
            
            // Load stylesheet asynchronously
            const deferredLink = document.createElement('link');
            deferredLink.rel = 'preload';
            deferredLink.as = 'style';
            deferredLink.href = href;
            deferredLink.onload = function() {
                this.onload = null;
                this.rel = 'stylesheet';
            };
            
            // Fallback for browsers that don't support preload
            deferredLink.onerror = function() {
                const fallbackLink = document.createElement('link');
                fallbackLink.rel = 'stylesheet';
                fallbackLink.href = href;
                document.head.appendChild(fallbackLink);
            };
            
            document.head.appendChild(deferredLink);
            
            // Remove original link after a delay
            setTimeout(() => {
                if (link.parentNode) {
                    link.parentNode.removeChild(link);
                }
            }, 100);
        });
    }
    
    optimizeJavaScriptLoading() {
        // Defer non-critical JavaScript
        const scripts = document.querySelectorAll('script[src]:not([data-critical])');
        
        scripts.forEach(script => {
            if (!script.hasAttribute('defer') && !script.hasAttribute('async')) {
                script.setAttribute('defer', 'true');
            }
        });
        
        // Load JavaScript modules efficiently
        this.loadJavaScriptModules();
    }
    
    loadJavaScriptModules() {
        // Define module loading priorities
        const moduleLoadOrder = [
            { src: '/static/js/accessibility-enhancements.js', priority: 'high' },
            { src: '/static/js/dashboard-hover-interactions.js', priority: 'medium' },
            { src: '/static/js/dynamic-visual-feedback.js', priority: 'medium' },
            { src: '/static/js/mobile-interactions.js', priority: 'low' }
        ];
        
        // Load modules based on priority
        this.loadModulesByPriority(moduleLoadOrder);
    }
    
    loadModulesByPriority(modules) {
        const highPriorityModules = modules.filter(m => m.priority === 'high');
        const mediumPriorityModules = modules.filter(m => m.priority === 'medium');
        const lowPriorityModules = modules.filter(m => m.priority === 'low');
        
        // Load high priority modules immediately
        highPriorityModules.forEach(module => {
            this.loadScript(module.src);
        });
        
        // Load medium priority modules after DOM content loaded
        document.addEventListener('DOMContentLoaded', () => {
            mediumPriorityModules.forEach(module => {
                this.loadScript(module.src);
            });
        });
        
        // Load low priority modules after window load
        window.addEventListener('load', () => {
            setTimeout(() => {
                lowPriorityModules.forEach(module => {
                    this.loadScript(module.src);
                });
            }, 1000);
        });
    }
    
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    preloadCriticalResources() {
        // Preload critical resources
        const criticalResources = [
            { href: '/static/images/carfinity logo.png', as: 'image' },
            { href: '/static/css/dashboard-hover-effects.css', as: 'style' }
        ];
        
        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource.href;
            link.as = resource.as;
            
            if (resource.as === 'image') {
                link.crossOrigin = 'anonymous';
            }
            
            document.head.appendChild(link);
        });
    }
    
    setupLazyLoading() {
        // Setup intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            this.setupIntersectionObserver();
        } else {
            // Fallback for browsers without IntersectionObserver
            this.setupFallbackLazyLoading();
        }
        
        // Lazy load images
        this.setupImageLazyLoading();
        
        // Lazy load content sections
        this.setupContentLazyLoading();
        
        // Lazy load third-party widgets
        this.setupWidgetLazyLoading();
    }
    
    setupIntersectionObserver() {
        // Observer for images
        this.imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    this.imageObserver.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        // Observer for content sections
        this.contentObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadContentSection(entry.target);
                    this.contentObserver.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '100px 0px',
            threshold: 0.1
        });
    }
    
    setupImageLazyLoading() {
        // Find all images that should be lazy loaded
        const lazyImages = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        
        lazyImages.forEach(img => {
            // Add loading placeholder
            this.addImagePlaceholder(img);
            
            // Observe image for lazy loading
            if (this.imageObserver) {
                this.imageObserver.observe(img);
            }
        });
    }
    
    addImagePlaceholder(img) {
        // Create placeholder element
        const placeholder = document.createElement('div');
        placeholder.className = 'image-placeholder skeleton';
        placeholder.style.cssText = `
            width: ${img.offsetWidth || 300}px;
            height: ${img.offsetHeight || 200}px;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 8px;
        `;
        
        // Insert placeholder before image
        img.parentNode.insertBefore(placeholder, img);
        
        // Hide original image
        img.style.display = 'none';
        
        // Store reference to placeholder
        img.dataset.placeholder = 'true';
    }
    
    loadImage(img) {
        return new Promise((resolve, reject) => {
            const actualSrc = img.dataset.src || img.src;
            
            // Create new image to preload
            const newImg = new Image();
            
            newImg.onload = () => {
                // Update original image
                img.src = actualSrc;
                img.style.display = '';
                
                // Remove placeholder
                const placeholder = img.previousElementSibling;
                if (placeholder && placeholder.classList.contains('image-placeholder')) {
                    placeholder.remove();
                }
                
                // Add fade-in animation
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease';
                
                requestAnimationFrame(() => {
                    img.style.opacity = '1';
                });
                
                resolve(img);
            };
            
            newImg.onerror = () => {
                // Handle image load error
                this.handleImageError(img);
                reject(new Error(`Failed to load image: ${actualSrc}`));
            };
            
            newImg.src = actualSrc;
        });
    }
    
    handleImageError(img) {
        // Create error placeholder
        const errorPlaceholder = document.createElement('div');
        errorPlaceholder.className = 'image-error-placeholder';
        errorPlaceholder.innerHTML = `
            <div class="flex items-center justify-center h-full bg-gray-100 rounded-lg">
                <div class="text-center">
                    <i class="fas fa-image text-gray-400 text-2xl mb-2"></i>
                    <p class="text-sm text-gray-500">Image not available</p>
                </div>
            </div>
        `;
        
        // Replace image with error placeholder
        img.parentNode.replaceChild(errorPlaceholder, img);
    }
    
    setupContentLazyLoading() {
        // Find content sections that should be lazy loaded
        const lazyContent = document.querySelectorAll('[data-lazy-load]');
        
        lazyContent.forEach(section => {
            // Add loading placeholder
            this.addContentPlaceholder(section);
            
            // Observe section for lazy loading
            if (this.contentObserver) {
                this.contentObserver.observe(section);
            }
        });
    }
    
    addContentPlaceholder(section) {
        const placeholder = document.createElement('div');
        placeholder.className = 'content-placeholder';
        placeholder.innerHTML = `
            <div class="animate-pulse">
                <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div class="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div class="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
        `;
        
        // Hide original content
        section.style.display = 'none';
        
        // Insert placeholder
        section.parentNode.insertBefore(placeholder, section);
    }
    
    loadContentSection(section) {
        // Show original content
        section.style.display = '';
        
        // Remove placeholder
        const placeholder = section.previousElementSibling;
        if (placeholder && placeholder.classList.contains('content-placeholder')) {
            placeholder.remove();
        }
        
        // Trigger content loaded event
        section.dispatchEvent(new CustomEvent('contentLoaded'));
    }
    
    setupWidgetLazyLoading() {
        // Lazy load third-party widgets and embeds
        const widgets = document.querySelectorAll('[data-widget-src]');
        
        widgets.forEach(widget => {
            if (this.contentObserver) {
                this.contentObserver.observe(widget);
            }
        });
    }
    
    setupImageOptimization() {
        // Optimize image loading
        this.setupResponsiveImages();
        this.setupImageCompression();
        this.setupWebPSupport();
    }
    
    setupResponsiveImages() {
        // Add responsive image support
        const images = document.querySelectorAll('img:not([srcset])');
        
        images.forEach(img => {
            const src = img.src || img.dataset.src;
            if (!src) return;
            
            // Generate responsive image sources
            const baseSrc = src.replace(/\.(jpg|jpeg|png|webp)$/i, '');
            const extension = src.match(/\.(jpg|jpeg|png|webp)$/i)?.[1] || 'jpg';
            
            // Create srcset for different screen densities
            const srcset = [
                `${baseSrc}_1x.${extension} 1x`,
                `${baseSrc}_2x.${extension} 2x`
            ].join(', ');
            
            img.setAttribute('srcset', srcset);
        });
    }
    
    setupImageCompression() {
        // Implement client-side image compression for uploads
        window.compressImage = (file, quality = 0.8) => {
            return new Promise((resolve) => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const img = new Image();
                
                img.onload = () => {
                    // Calculate new dimensions
                    const maxWidth = 1200;
                    const maxHeight = 800;
                    let { width, height } = img;
                    
                    if (width > maxWidth) {
                        height = (height * maxWidth) / width;
                        width = maxWidth;
                    }
                    
                    if (height > maxHeight) {
                        width = (width * maxHeight) / height;
                        height = maxHeight;
                    }
                    
                    // Set canvas dimensions
                    canvas.width = width;
                    canvas.height = height;
                    
                    // Draw and compress image
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    canvas.toBlob(resolve, 'image/jpeg', quality);
                };
                
                img.src = URL.createObjectURL(file);
            });
        };
    }
    
    setupWebPSupport() {
        // Check WebP support and use WebP images when available
        const supportsWebP = this.checkWebPSupport();
        
        if (supportsWebP) {
            const images = document.querySelectorAll('img[src*=".jpg"], img[src*=".jpeg"], img[src*=".png"]');
            
            images.forEach(img => {
                const src = img.src || img.dataset.src;
                const webpSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
                
                // Test if WebP version exists
                this.testImageExists(webpSrc).then(exists => {
                    if (exists) {
                        if (img.dataset.src) {
                            img.dataset.src = webpSrc;
                        } else {
                            img.src = webpSrc;
                        }
                    }
                });
            });
        }
    }
    
    checkWebPSupport() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }
    
    testImageExists(src) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(true);
            img.onerror = () => resolve(false);
            img.src = src;
        });
    }
    
    setupLoadingStates() {
        // Create global loading state management
        this.createLoadingStateManager();
        
        // Setup component loading states
        this.setupComponentLoadingStates();
        
        // Setup form loading states
        this.setupFormLoadingStates();
        
        // Setup AJAX loading states
        this.setupAjaxLoadingStates();
    }
    
    createLoadingStateManager() {
        window.LoadingManager = {
            show: (element, message = 'Loading...') => {
                return this.showLoadingState(element, message);
            },
            hide: (element) => {
                return this.hideLoadingState(element);
            },
            showGlobal: (message = 'Loading...') => {
                return this.showGlobalLoadingState(message);
            },
            hideGlobal: () => {
                return this.hideGlobalLoadingState();
            }
        };
    }
    
    showLoadingState(element, message) {
        const loadingId = `loading-${Date.now()}`;
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.id = loadingId;
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <span class="loading-message">${message}</span>
            </div>
        `;
        
        // Style the overlay
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            border-radius: inherit;
        `;
        
        // Ensure element has relative positioning
        const originalPosition = element.style.position;
        if (!originalPosition || originalPosition === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(overlay);
        
        // Store loading state
        this.loadingStates.set(element, {
            id: loadingId,
            originalPosition,
            startTime: Date.now()
        });
        
        return loadingId;
    }
    
    hideLoadingState(element) {
        const loadingState = this.loadingStates.get(element);
        if (!loadingState) return;
        
        const overlay = document.getElementById(loadingState.id);
        if (overlay) {
            // Add fade out animation
            overlay.style.transition = 'opacity 0.3s ease';
            overlay.style.opacity = '0';
            
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                
                // Restore original position
                if (!loadingState.originalPosition || loadingState.originalPosition === 'static') {
                    element.style.position = '';
                }
            }, 300);
        }
        
        this.loadingStates.delete(element);
    }
    
    showGlobalLoadingState(message) {
        let globalLoader = document.getElementById('global-loading-overlay');
        
        if (!globalLoader) {
            globalLoader = document.createElement('div');
            globalLoader.id = 'global-loading-overlay';
            globalLoader.innerHTML = `
                <div class="global-loading-content">
                    <div class="global-loading-spinner"></div>
                    <span class="global-loading-message">${message}</span>
                </div>
            `;
            
            globalLoader.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.95);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            
            document.body.appendChild(globalLoader);
        }
        
        // Show with animation
        requestAnimationFrame(() => {
            globalLoader.style.opacity = '1';
        });
        
        return globalLoader;
    }
    
    hideGlobalLoadingState() {
        const globalLoader = document.getElementById('global-loading-overlay');
        if (globalLoader) {
            globalLoader.style.opacity = '0';
            
            setTimeout(() => {
                if (globalLoader.parentNode) {
                    globalLoader.parentNode.removeChild(globalLoader);
                }
            }, 300);
        }
    }
    
    setupComponentLoadingStates() {
        // Add loading states to dashboard components
        const components = document.querySelectorAll('[data-component]');
        
        components.forEach(component => {
            const componentType = component.dataset.component;
            
            // Show loading state initially
            this.showLoadingState(component, `Loading ${componentType}...`);
            
            // Hide loading state when component is ready
            component.addEventListener('componentReady', () => {
                this.hideLoadingState(component);
            });
        });
    }
    
    setupFormLoadingStates() {
        // Add loading states to forms
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                
                if (submitButton) {
                    this.showButtonLoadingState(submitButton);
                }
            });
        });
    }
    
    showButtonLoadingState(button) {
        const originalText = button.textContent || button.value;
        const originalDisabled = button.disabled;
        
        button.disabled = true;
        button.classList.add('loading');
        
        if (button.tagName === 'BUTTON') {
            button.innerHTML = `
                <i class="fas fa-spinner fa-spin mr-2"></i>
                Loading...
            `;
        } else {
            button.value = 'Loading...';
        }
        
        // Store original state
        button.dataset.originalText = originalText;
        button.dataset.originalDisabled = originalDisabled;
    }
    
    hideButtonLoadingState(button) {
        const originalText = button.dataset.originalText;
        const originalDisabled = button.dataset.originalDisabled === 'true';
        
        button.disabled = originalDisabled;
        button.classList.remove('loading');
        
        if (button.tagName === 'BUTTON') {
            button.textContent = originalText;
        } else {
            button.value = originalText;
        }
        
        delete button.dataset.originalText;
        delete button.dataset.originalDisabled;
    }
    
    setupAjaxLoadingStates() {
        // Intercept fetch requests to show loading states
        const originalFetch = window.fetch;
        
        window.fetch = (...args) => {
            const loadingId = this.showGlobalLoadingState('Loading...');
            
            return originalFetch(...args)
                .then(response => {
                    this.hideGlobalLoadingState();
                    return response;
                })
                .catch(error => {
                    this.hideGlobalLoadingState();
                    this.handleFetchError(error);
                    throw error;
                });
        };
    }
    
    setupErrorHandling() {
        // Global error handling
        this.setupGlobalErrorHandler();
        
        // Network error handling
        this.setupNetworkErrorHandler();
        
        // Resource loading error handling
        this.setupResourceErrorHandler();
        
        // JavaScript error handling
        this.setupJavaScriptErrorHandler();
    }
    
    setupGlobalErrorHandler() {
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event.error, event.filename, event.lineno);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection(event.reason);
        });
    }
    
    handleGlobalError(error, filename, lineno) {
        console.error('Global error:', error, filename, lineno);
        
        // Show user-friendly error message
        this.showErrorNotification('An unexpected error occurred. Please refresh the page.');
        
        // Log error for monitoring
        this.logError('global', error, { filename, lineno });
    }
    
    handlePromiseRejection(reason) {
        console.error('Unhandled promise rejection:', reason);
        
        // Show user-friendly error message
        this.showErrorNotification('A network error occurred. Please check your connection.');
        
        // Log error for monitoring
        this.logError('promise', reason);
    }
    
    setupNetworkErrorHandler() {
        // Handle network connectivity issues
        window.addEventListener('online', () => {
            this.showSuccessNotification('Connection restored');
            this.retryFailedRequests();
        });
        
        window.addEventListener('offline', () => {
            this.showErrorNotification('Connection lost. Some features may not work.');
        });
    }
    
    setupResourceErrorHandler() {
        // Handle resource loading errors
        document.addEventListener('error', (event) => {
            if (event.target.tagName === 'IMG') {
                this.handleImageError(event.target);
            } else if (event.target.tagName === 'SCRIPT') {
                this.handleScriptError(event.target);
            } else if (event.target.tagName === 'LINK') {
                this.handleStylesheetError(event.target);
            }
        }, true);
    }
    
    handleScriptError(script) {
        console.error('Script loading error:', script.src);
        
        // Try to load fallback or retry
        this.retryResourceLoad(script);
    }
    
    handleStylesheetError(link) {
        console.error('Stylesheet loading error:', link.href);
        
        // Try to load fallback or retry
        this.retryResourceLoad(link);
    }
    
    retryResourceLoad(element, maxRetries = 3) {
        const retryCount = parseInt(element.dataset.retryCount || '0');
        
        if (retryCount < maxRetries) {
            element.dataset.retryCount = (retryCount + 1).toString();
            
            setTimeout(() => {
                if (element.tagName === 'SCRIPT') {
                    const newScript = document.createElement('script');
                    newScript.src = element.src;
                    newScript.dataset.retryCount = element.dataset.retryCount;
                    document.head.appendChild(newScript);
                } else if (element.tagName === 'LINK') {
                    const newLink = document.createElement('link');
                    newLink.rel = element.rel;
                    newLink.href = element.href;
                    newLink.dataset.retryCount = element.dataset.retryCount;
                    document.head.appendChild(newLink);
                }
            }, 1000 * retryCount);
        }
    }
    
    setupJavaScriptErrorHandler() {
        // Handle JavaScript runtime errors gracefully
        window.onerror = (message, source, lineno, colno, error) => {
            this.handleJavaScriptError(error || new Error(message), source, lineno);
            return true; // Prevent default browser error handling
        };
    }
    
    handleJavaScriptError(error, source, lineno) {
        console.error('JavaScript error:', error, source, lineno);
        
        // Don't show error notification for minor errors
        if (this.isCriticalError(error)) {
            this.showErrorNotification('A technical error occurred. Some features may not work properly.');
        }
        
        // Log error for monitoring
        this.logError('javascript', error, { source, lineno });
    }
    
    isCriticalError(error) {
        const criticalPatterns = [
            /network/i,
            /fetch/i,
            /xhr/i,
            /timeout/i,
            /cors/i
        ];
        
        return criticalPatterns.some(pattern => pattern.test(error.message));
    }
    
    handleFetchError(error) {
        console.error('Fetch error:', error);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            this.showErrorNotification('Network error. Please check your connection.');
        } else {
            this.showErrorNotification('Request failed. Please try again.');
        }
    }
    
    showErrorNotification(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccessNotification(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                <span>${message}</span>
                <button class="notification-close" aria-label="Close notification">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#fee' : type === 'success' ? '#efe' : '#eef'};
            border: 1px solid ${type === 'error' ? '#fcc' : type === 'success' ? '#cfc' : '#ccf'};
            color: ${type === 'error' ? '#c33' : type === 'success' ? '#3c3' : '#33c'};
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 10000;
            max-width: 400px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Show notification
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
        });
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);
        
        // Close button handler
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            this.hideNotification(notification);
        });
    }
    
    hideNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
    
    logError(type, error, context = {}) {
        // Log error to monitoring service (implement based on your monitoring solution)
        const errorData = {
            type,
            message: error.message,
            stack: error.stack,
            context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        // Send to monitoring service
        if (window.errorLogger) {
            window.errorLogger.log(errorData);
        } else {
            console.log('Error logged:', errorData);
        }
    }
    
    setupResourcePreloading() {
        // Preload resources based on user behavior
        this.setupPredictivePreloading();
        
        // Preload next page resources
        this.setupNextPagePreloading();
        
        // Preload critical images
        this.setupCriticalImagePreloading();
    }
    
    setupPredictivePreloading() {
        // Preload resources when user hovers over links
        const links = document.querySelectorAll('a[href]');
        
        links.forEach(link => {
            let preloadTimeout;
            
            link.addEventListener('mouseenter', () => {
                preloadTimeout = setTimeout(() => {
                    this.preloadPage(link.href);
                }, 200);
            });
            
            link.addEventListener('mouseleave', () => {
                clearTimeout(preloadTimeout);
            });
        });
    }
    
    preloadPage(url) {
        // Preload page resources
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }
    
    setupNextPagePreloading() {
        // Preload likely next pages based on navigation patterns
        const navigationLinks = document.querySelectorAll('.nav-item, .navigation a');
        
        navigationLinks.forEach(link => {
            // Preload on intersection (when link becomes visible)
            if (this.contentObserver) {
                this.contentObserver.observe(link);
            }
        });
    }
    
    setupCriticalImagePreloading() {
        // Preload images that are likely to be needed
        const criticalImages = [
            '/static/images/carfinity logo.png',
            '/static/images/default-vehicle.png'
        ];
        
        criticalImages.forEach(src => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = src;
            document.head.appendChild(link);
        });
    }
    
    setupPerformanceMonitoring() {
        // Monitor performance metrics
        this.monitorPageLoadTime();
        this.monitorResourceLoadTime();
        this.monitorUserInteractions();
        this.monitorMemoryUsage();
    }
    
    monitorPageLoadTime() {
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`Page load time: ${loadTime.toFixed(2)}ms`);
            
            // Log to analytics
            this.logPerformanceMetric('page_load_time', loadTime);
        });
    }
    
    monitorResourceLoadTime() {
        // Monitor resource loading performance
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.duration > 1000) { // Log slow resources
                    console.warn(`Slow resource: ${entry.name} took ${entry.duration.toFixed(2)}ms`);
                    this.logPerformanceMetric('slow_resource', entry.duration, { resource: entry.name });
                }
            });
        });
        
        observer.observe({ entryTypes: ['resource'] });
    }
    
    monitorUserInteractions() {
        // Monitor interaction performance
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                if (entry.processingStart - entry.startTime > 100) {
                    console.warn(`Slow interaction: ${entry.name} took ${(entry.processingStart - entry.startTime).toFixed(2)}ms`);
                }
            });
        });
        
        if ('PerformanceEventTiming' in window) {
            observer.observe({ entryTypes: ['event'] });
        }
    }
    
    monitorMemoryUsage() {
        // Monitor memory usage if available
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1024 / 1024;
                
                if (usedMB > 50) { // Log high memory usage
                    console.warn(`High memory usage: ${usedMB.toFixed(2)}MB`);
                    this.logPerformanceMetric('high_memory_usage', usedMB);
                }
            }, 30000); // Check every 30 seconds
        }
    }
    
    logPerformanceMetric(metric, value, context = {}) {
        // Log performance metric to analytics service
        const metricData = {
            metric,
            value,
            context,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
        
        if (window.analytics) {
            window.analytics.track('performance_metric', metricData);
        } else {
            console.log('Performance metric:', metricData);
        }
    }
    
    setupCacheOptimization() {
        // Implement service worker for caching
        this.registerServiceWorker();
        
        // Setup localStorage caching
        this.setupLocalStorageCache();
        
        // Setup sessionStorage caching
        this.setupSessionStorageCache();
    }
    
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }
    
    setupLocalStorageCache() {
        // Cache static data in localStorage
        window.CacheManager = {
            set: (key, data, ttl = 3600000) => { // 1 hour default TTL
                const item = {
                    data,
                    timestamp: Date.now(),
                    ttl
                };
                localStorage.setItem(key, JSON.stringify(item));
            },
            
            get: (key) => {
                const item = localStorage.getItem(key);
                if (!item) return null;
                
                const parsed = JSON.parse(item);
                if (Date.now() - parsed.timestamp > parsed.ttl) {
                    localStorage.removeItem(key);
                    return null;
                }
                
                return parsed.data;
            },
            
            remove: (key) => {
                localStorage.removeItem(key);
            },
            
            clear: () => {
                localStorage.clear();
            }
        };
    }
    
    setupSessionStorageCache() {
        // Cache session data in sessionStorage
        window.SessionCache = {
            set: (key, data) => {
                sessionStorage.setItem(key, JSON.stringify(data));
            },
            
            get: (key) => {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            },
            
            remove: (key) => {
                sessionStorage.removeItem(key);
            },
            
            clear: () => {
                sessionStorage.clear();
            }
        };
    }
    
    retryFailedRequests() {
        // Retry failed requests when connection is restored
        // This would integrate with your request queue system
        console.log('Retrying failed requests...');
    }
    
    // Public API methods
    optimizeImages() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.dataset.optimized) {
                this.loadImage(img);
                img.dataset.optimized = 'true';
            }
        });
    }
    
    preloadResource(url, type = 'fetch') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = url;
        link.as = type;
        document.head.appendChild(link);
    }
    
    // Cleanup method
    destroy() {
        if (this.imageObserver) {
            this.imageObserver.disconnect();
        }
        
        if (this.contentObserver) {
            this.contentObserver.disconnect();
        }
        
        this.loadingStates.clear();
        this.isInitialized = false;
    }
}

// Loading spinner CSS
const loadingSpinnerCSS = `
.loading-spinner,
.global-loading-spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid #e5e7eb;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.global-loading-spinner {
    width: 3rem;
    height: 3rem;
    border-width: 3px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-content,
.global-loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.loading-message,
.global-loading-message {
    color: #6b7280;
    font-weight: 500;
}

.global-loading-message {
    font-size: 1.125rem;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.notification-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    opacity: 0.7;
    transition: opacity 0.2s;
}

.notification-close:hover {
    opacity: 1;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    .loading-spinner,
    .global-loading-spinner {
        animation: none;
    }
    
    .loading-overlay,
    .global-loading-overlay,
    .notification {
        transition: none !important;
    }
}
`;

// Inject loading spinner CSS
const loadingStyleSheet = document.createElement('style');
loadingStyleSheet.textContent = loadingSpinnerCSS;
document.head.appendChild(loadingStyleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.performanceOptimization = new PerformanceOptimization();
});

// Export for external use
window.PerformanceOptimization = PerformanceOptimization;