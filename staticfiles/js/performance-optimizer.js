/**
 * Performance Optimizer
 * Handles CSS/JS minification, image optimization, lazy loading, and caching strategies
 */

class PerformanceOptimizer {
    constructor() {
        this.cache = new Map();
        this.imageCache = new Map();
        this.lazyImages = [];
        this.preloadQueue = [];
        this.compressionEnabled = true;
        
        this.init().catch(error => {
            console.error('Performance optimizer initialization failed:', error);
        });
    }
    
    async init() {
        this.setupLazyLoading();
        this.setupImageOptimization();
        this.setupResourceCaching();
        this.setupPreloading();
        await this.setupCompressionDetection();
        this.setupPerformanceMonitoring();
        this.optimizeExistingResources();
    }
    
    setupLazyLoading() {
        // Lazy load images
        this.setupImageLazyLoading();
        
        // Lazy load components
        this.setupComponentLazyLoading();
        
        // Lazy load scripts
        this.setupScriptLazyLoading();
    }
    
    setupImageLazyLoading() {
        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        imageObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });
            
            images.forEach(img => {
                imageObserver.observe(img);
                this.lazyImages.push(img);
            });
        } else {
            // Fallback for older browsers
            images.forEach(img => this.loadImage(img));
        }
    }
    
    setupComponentLazyLoading() {
        const lazyComponents = document.querySelectorAll('[data-lazy-component]');
        
        if ('IntersectionObserver' in window) {
            const componentObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadComponent(entry.target);
                        componentObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '100px 0px',
                threshold: 0.01
            });
            
            lazyComponents.forEach(component => {
                componentObserver.observe(component);
            });
        }
    }
    
    setupScriptLazyLoading() {
        const lazyScripts = document.querySelectorAll('script[data-lazy]');
        
        lazyScripts.forEach(script => {
            const newScript = document.createElement('script');
            newScript.src = script.dataset.src || script.src;
            newScript.async = true;
            
            // Load script when needed
            if (script.dataset.trigger) {
                document.addEventListener(script.dataset.trigger, () => {
                    document.head.appendChild(newScript);
                }, { once: true });
            } else {
                // Load after page load
                window.addEventListener('load', () => {
                    setTimeout(() => {
                        document.head.appendChild(newScript);
                    }, 1000);
                });
            }
        });
    }
    
    setupImageOptimization() {
        // WebP support detection
        this.detectWebPSupport().then(supported => {
            this.webpSupported = supported;
            this.optimizeImages();
        });
        
        // Responsive image loading
        this.setupResponsiveImages();
    }
    
    detectWebPSupport() {
        return new Promise(resolve => {
            const webP = new Image();
            webP.onload = webP.onerror = () => {
                resolve(webP.height === 2);
            };
            webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
        });
    }
    
    setupResponsiveImages() {
        const responsiveImages = document.querySelectorAll('img[data-sizes]');
        
        responsiveImages.forEach(img => {
            this.optimizeImageForViewport(img);
        });
        
        // Update on resize
        window.addEventListener('resize', this.debounce(() => {
            responsiveImages.forEach(img => {
                this.optimizeImageForViewport(img);
            });
        }, 250));
    }
    
    setupResourceCaching() {
        // Service Worker registration for caching
        if ('serviceWorker' in navigator) {
            this.registerServiceWorker();
        }
        
        // Memory caching for API responses
        this.setupAPICache();
        
        // Local storage caching for user preferences
        this.setupLocalStorageCache();
    }
    
    registerServiceWorker() {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker registered:', registration);
                this.serviceWorkerRegistration = registration;
            })
            .catch(error => {
                console.log('Service Worker registration failed:', error);
            });
    }
    
    setupAPICache() {
        // Cache API responses in memory
        const originalFetch = window.fetch;
        
        window.fetch = async (url, options = {}) => {
            const cacheKey = `${url}_${JSON.stringify(options)}`;
            
            // Check cache first for GET requests
            if (!options.method || options.method === 'GET') {
                const cached = this.cache.get(cacheKey);
                if (cached && !this.isCacheExpired(cached)) {
                    return Promise.resolve(new Response(JSON.stringify(cached.data), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    }));
                }
            }
            
            // Make actual request
            const response = await originalFetch(url, options);
            
            // Cache successful GET responses
            if (response.ok && (!options.method || options.method === 'GET')) {
                const clonedResponse = response.clone();
                clonedResponse.json().then(data => {
                    this.cache.set(cacheKey, {
                        data: data,
                        timestamp: Date.now(),
                        ttl: 5 * 60 * 1000 // 5 minutes
                    });
                }).catch(() => {
                    // Ignore JSON parsing errors
                });
            }
            
            return response;
        };
    }
    
    setupLocalStorageCache() {
        // Cache user preferences and settings
        this.userCache = {
            get: (key) => {
                try {
                    const item = localStorage.getItem(`perf_cache_${key}`);
                    if (item) {
                        const parsed = JSON.parse(item);
                        if (!this.isCacheExpired(parsed)) {
                            return parsed.data;
                        } else {
                            localStorage.removeItem(`perf_cache_${key}`);
                        }
                    }
                } catch (e) {
                    console.warn('Cache retrieval error:', e);
                }
                return null;
            },
            
            set: (key, data, ttl = 24 * 60 * 60 * 1000) => {
                try {
                    const item = {
                        data: data,
                        timestamp: Date.now(),
                        ttl: ttl
                    };
                    localStorage.setItem(`perf_cache_${key}`, JSON.stringify(item));
                } catch (e) {
                    console.warn('Cache storage error:', e);
                }
            },
            
            clear: () => {
                Object.keys(localStorage).forEach(key => {
                    if (key.startsWith('perf_cache_')) {
                        localStorage.removeItem(key);
                    }
                });
            }
        };
    }
    
    setupPreloading() {
        // Preload critical resources
        this.preloadCriticalResources();
        
        // Prefetch likely next pages
        this.setupPrefetching();
        
        // DNS prefetch for external resources
        this.setupDNSPrefetch();
    }
    
    preloadCriticalResources() {
        const criticalResources = [
            { href: '/static/css/dashboard-integration.css', as: 'style' },
            { href: '/static/js/dashboard-navigation.js', as: 'script' },
            { href: '/static/js/notifications.js', as: 'script' }
        ];
        
        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource.href;
            link.as = resource.as;
            if (resource.type) link.type = resource.type;
            document.head.appendChild(link);
        });
    }
    
    setupPrefetching() {
        // Prefetch pages on hover
        const internalLinks = document.querySelectorAll('a[href^="/insurance/"]');
        
        internalLinks.forEach(link => {
            link.addEventListener('mouseenter', () => {
                this.prefetchPage(link.href);
            }, { once: true });
        });
        
        // Prefetch based on user behavior
        this.setupIntelligentPrefetching();
    }
    
    setupIntelligentPrefetching() {
        // Track user navigation patterns
        const navigationHistory = JSON.parse(localStorage.getItem('navigationHistory') || '[]');
        
        // Predict likely next pages based on current page
        const currentPage = window.location.pathname;
        const predictions = this.predictNextPages(currentPage, navigationHistory);
        
        // Prefetch predicted pages
        predictions.forEach(page => {
            setTimeout(() => {
                this.prefetchPage(page);
            }, 2000); // Wait 2 seconds before prefetching
        });
    }
    
    setupDNSPrefetch() {
        const externalDomains = [
            'cdn.tailwindcss.com',
            'cdnjs.cloudflare.com',
            'fonts.googleapis.com'
        ];
        
        externalDomains.forEach(domain => {
            const link = document.createElement('link');
            link.rel = 'dns-prefetch';
            link.href = `//${domain}`;
            document.head.appendChild(link);
        });
    }
    
    async setupCompressionDetection() {
        // Detect if compression is supported
        try {
            this.compressionSupport = {
                gzip: await this.checkCompressionSupport('gzip'),
                brotli: await this.checkCompressionSupport('br')
            };
        } catch (error) {
            console.warn('Compression detection failed:', error);
            this.compressionSupport = {
                gzip: false,
                brotli: false
            };
        }
    }
    
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        this.monitorCoreWebVitals();
        
        // Monitor resource loading
        this.monitorResourceLoading();
        
        // Monitor user interactions
        this.monitorUserInteractions();
    }
    
    optimizeExistingResources() {
        // Optimize CSS delivery
        this.optimizeCSSDelivery();
        
        // Optimize JavaScript execution
        this.optimizeJavaScriptExecution();
        
        // Optimize font loading
        this.optimizeFontLoading();
    }
    
    // Implementation methods
    loadImage(img) {
        const src = img.dataset.src || img.src;
        
        if (this.webpSupported && img.dataset.webp) {
            img.src = img.dataset.webp;
        } else {
            img.src = src;
        }
        
        img.classList.remove('loading-skeleton');
        img.classList.add('fade-in');
        
        // Remove data-src to prevent reloading
        delete img.dataset.src;
    }
    
    loadComponent(component) {
        const componentType = component.dataset.lazyComponent;
        
        switch (componentType) {
            case 'chart':
                this.loadChartComponent(component);
                break;
            case 'map':
                this.loadMapComponent(component);
                break;
            case 'table':
                this.loadTableComponent(component);
                break;
            default:
                this.loadGenericComponent(component);
        }
    }
    
    loadChartComponent(component) {
        // Load chart library and render chart
        if (!window.Chart) {
            this.loadScript('https://cdn.jsdelivr.net/npm/chart.js').then(() => {
                this.renderChart(component);
            });
        } else {
            this.renderChart(component);
        }
    }
    
    loadMapComponent(component) {
        // Load map library and render map
        if (!window.L) {
            this.loadScript('https://unpkg.com/leaflet/dist/leaflet.js').then(() => {
                this.renderMap(component);
            });
        } else {
            this.renderMap(component);
        }
    }
    
    loadTableComponent(component) {
        // Load table data and render
        const dataUrl = component.dataset.dataUrl;
        if (dataUrl) {
            fetch(dataUrl)
                .then(response => response.json())
                .then(data => this.renderTable(component, data));
        }
    }
    
    loadGenericComponent(component) {
        component.classList.remove('loading-skeleton');
        component.classList.add('fade-in');
    }
    
    optimizeImageForViewport(img) {
        const viewport = this.getViewportSize();
        const sizes = JSON.parse(img.dataset.sizes || '{}');
        
        let optimalSrc = img.src;
        
        // Choose optimal image size based on viewport
        if (viewport.width <= 480 && sizes.small) {
            optimalSrc = sizes.small;
        } else if (viewport.width <= 768 && sizes.medium) {
            optimalSrc = sizes.medium;
        } else if (sizes.large) {
            optimalSrc = sizes.large;
        }
        
        if (optimalSrc !== img.src) {
            img.src = optimalSrc;
        }
    }
    
    prefetchPage(url) {
        if (this.preloadQueue.includes(url)) return;
        
        this.preloadQueue.push(url);
        
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }
    
    predictNextPages(currentPage, history) {
        const predictions = [];
        
        // Simple prediction based on common navigation patterns
        if (currentPage.includes('/insurance/')) {
            if (!currentPage.includes('/assessments/')) {
                predictions.push('/insurance/assessments/');
            }
            if (!currentPage.includes('/book-assessment/')) {
                predictions.push('/insurance/book-assessment/');
            }
        }
        
        // Add predictions based on history
        const recentPages = history.slice(-10);
        const pageFrequency = {};
        
        recentPages.forEach(entry => {
            pageFrequency[entry.url] = (pageFrequency[entry.url] || 0) + 1;
        });
        
        const sortedPages = Object.entries(pageFrequency)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 2)
            .map(([url]) => url);
        
        predictions.push(...sortedPages);
        
        return [...new Set(predictions)]; // Remove duplicates
    }
    
    checkCompressionSupport(encoding) {
        // Use fetch API instead of XMLHttpRequest to avoid unsafe header error
        return fetch(window.location.href, {
            method: 'HEAD',
            headers: {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        }).then(response => {
            return response.headers.get('Content-Encoding') === encoding;
        }).catch(() => {
            return false;
        });
    }
    
    monitorCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                console.log('LCP:', lastEntry.startTime);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            
            // First Input Delay (FID)
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    console.log('FID:', entry.processingStart - entry.startTime);
                });
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
            
            // Cumulative Layout Shift (CLS)
            let clsValue = 0;
            const clsObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                console.log('CLS:', clsValue);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
        }
    }
    
    monitorResourceLoading() {
        if ('PerformanceObserver' in window) {
            const resourceObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.duration > 1000) { // Slow resource
                        console.warn('Slow resource:', entry.name, entry.duration);
                    }
                });
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
        }
    }
    
    monitorUserInteractions() {
        let interactionCount = 0;
        
        ['click', 'keydown', 'scroll'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                interactionCount++;
            }, { passive: true });
        });
        
        // Report interaction metrics periodically
        setInterval(() => {
            if (interactionCount > 0) {
                console.log('User interactions in last minute:', interactionCount);
                interactionCount = 0;
            }
        }, 60000);
    }
    
    optimizeCSSDelivery() {
        // Move non-critical CSS to load asynchronously
        const nonCriticalCSS = document.querySelectorAll('link[rel="stylesheet"][data-critical="false"]');
        
        nonCriticalCSS.forEach(link => {
            link.media = 'print';
            link.onload = function() {
                this.media = 'all';
            };
        });
    }
    
    optimizeJavaScriptExecution() {
        // Defer non-critical JavaScript
        const nonCriticalScripts = document.querySelectorAll('script[data-critical="false"]');
        
        nonCriticalScripts.forEach(script => {
            script.defer = true;
        });
    }
    
    optimizeFontLoading() {
        // Preload critical fonts
        const criticalFonts = [
            '/static/fonts/inter-regular.woff2',
            '/static/fonts/inter-medium.woff2'
        ];
        
        criticalFonts.forEach(font => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = font;
            link.as = 'font';
            link.type = 'font/woff2';
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }
    
    // Utility methods
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    getViewportSize() {
        return {
            width: window.innerWidth || document.documentElement.clientWidth,
            height: window.innerHeight || document.documentElement.clientHeight
        };
    }
    
    isCacheExpired(cacheItem) {
        return Date.now() - cacheItem.timestamp > cacheItem.ttl;
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
    
    // Public API
    clearCache() {
        this.cache.clear();
        this.imageCache.clear();
        this.userCache.clear();
    }
    
    getPerformanceMetrics() {
        if ('performance' in window) {
            return {
                navigation: performance.getEntriesByType('navigation')[0],
                resources: performance.getEntriesByType('resource'),
                memory: performance.memory
            };
        }
        return null;
    }
    
    optimizeImage(img, options = {}) {
        return this.optimizeImageForViewport(img);
    }
    
    preloadResource(url, type = 'fetch') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = url;
        link.as = type;
        document.head.appendChild(link);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.performanceOptimizer = new PerformanceOptimizer();
});

// Export for external use
window.PerformanceOptimizer = PerformanceOptimizer;