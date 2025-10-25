/**
 * Performance Validation Suite
 * Comprehensive performance testing and optimization validation
 */

class PerformanceValidator {
    constructor() {
        this.metrics = {};
        this.thresholds = {
            // Core Web Vitals
            LCP: 2500, // Largest Contentful Paint (ms)
            FID: 100,  // First Input Delay (ms)
            CLS: 0.1,  // Cumulative Layout Shift
            
            // Additional metrics
            FCP: 1800, // First Contentful Paint (ms)
            TTI: 3800, // Time to Interactive (ms)
            TBT: 200,  // Total Blocking Time (ms)
            
            // Resource metrics
            totalSize: 2000000, // 2MB total page size
            imageSize: 1000000, // 1MB total image size
            jsSize: 500000,     // 500KB total JS size
            cssSize: 100000,    // 100KB total CSS size
            
            // Performance scores
            performanceScore: 90,
            accessibilityScore: 90,
            bestPracticesScore: 90,
            seoScore: 90
        };
        
        this.issues = [];
        this.optimizations = [];
        this.passes = [];
        
        this.init();
    }

    init() {
        console.log('Starting performance validation...');
        this.measureCoreWebVitals();
        this.analyzeResourceLoading();
        this.testImageOptimization();
        this.validateCaching();
        this.checkJavaScriptPerformance();
        this.analyzeCSSPerformance();
        this.testMobilePerformance();
        this.generatePerformanceReport();
    }

    measureCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            try {
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.metrics.LCP = lastEntry.startTime;
                    
                    if (this.metrics.LCP > this.thresholds.LCP) {
                        this.issues.push({
                            type: 'lcp-slow',
                            metric: 'LCP',
                            value: this.metrics.LCP,
                            threshold: this.thresholds.LCP,
                            message: `Largest Contentful Paint is slow: ${this.metrics.LCP.toFixed(0)}ms (target: <${this.thresholds.LCP}ms)`,
                            impact: 'high'
                        });
                    } else {
                        this.passes.push({
                            test: 'Largest Contentful Paint',
                            message: `LCP: ${this.metrics.LCP.toFixed(0)}ms (Good)`
                        });
                    }
                });
                
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (error) {
                console.warn('LCP measurement failed:', error);
            }

            // First Input Delay (FID)
            try {
                const fidObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        this.metrics.FID = entry.processingStart - entry.startTime;
                        
                        if (this.metrics.FID > this.thresholds.FID) {
                            this.issues.push({
                                type: 'fid-slow',
                                metric: 'FID',
                                value: this.metrics.FID,
                                threshold: this.thresholds.FID,
                                message: `First Input Delay is slow: ${this.metrics.FID.toFixed(0)}ms (target: <${this.thresholds.FID}ms)`,
                                impact: 'high'
                            });
                        } else {
                            this.passes.push({
                                test: 'First Input Delay',
                                message: `FID: ${this.metrics.FID.toFixed(0)}ms (Good)`
                            });
                        }
                    });
                });
                
                fidObserver.observe({ entryTypes: ['first-input'] });
            } catch (error) {
                console.warn('FID measurement failed:', error);
            }

            // Cumulative Layout Shift (CLS)
            try {
                let clsValue = 0;
                const clsObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    });
                    
                    this.metrics.CLS = clsValue;
                    
                    if (this.metrics.CLS > this.thresholds.CLS) {
                        this.issues.push({
                            type: 'cls-high',
                            metric: 'CLS',
                            value: this.metrics.CLS,
                            threshold: this.thresholds.CLS,
                            message: `Cumulative Layout Shift is high: ${this.metrics.CLS.toFixed(3)} (target: <${this.thresholds.CLS})`,
                            impact: 'medium'
                        });
                    } else {
                        this.passes.push({
                            test: 'Cumulative Layout Shift',
                            message: `CLS: ${this.metrics.CLS.toFixed(3)} (Good)`
                        });
                    }
                });
                
                clsObserver.observe({ entryTypes: ['layout-shift'] });
            } catch (error) {
                console.warn('CLS measurement failed:', error);
            }
        }

        // Navigation Timing API metrics
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            
            // First Contentful Paint (approximate)
            this.metrics.FCP = timing.domContentLoadedEventEnd - timing.navigationStart;
            
            // Time to Interactive (approximate)
            this.metrics.TTI = timing.loadEventEnd - timing.navigationStart;
            
            // Page Load Time
            this.metrics.loadTime = timing.loadEventEnd - timing.navigationStart;
            
            // DOM Ready Time
            this.metrics.domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
            
            // Validate metrics
            if (this.metrics.FCP > this.thresholds.FCP) {
                this.issues.push({
                    type: 'fcp-slow',
                    metric: 'FCP',
                    value: this.metrics.FCP,
                    threshold: this.thresholds.FCP,
                    message: `First Contentful Paint is slow: ${this.metrics.FCP}ms (target: <${this.thresholds.FCP}ms)`,
                    impact: 'medium'
                });
            }
            
            if (this.metrics.TTI > this.thresholds.TTI) {
                this.issues.push({
                    type: 'tti-slow',
                    metric: 'TTI',
                    value: this.metrics.TTI,
                    threshold: this.thresholds.TTI,
                    message: `Time to Interactive is slow: ${this.metrics.TTI}ms (target: <${this.thresholds.TTI}ms)`,
                    impact: 'high'
                });
            }
        }
    }

    analyzeResourceLoading() {
        if (!window.performance || !window.performance.getEntriesByType) return;
        
        const resources = window.performance.getEntriesByType('resource');
        let totalSize = 0;
        let imageSize = 0;
        let jsSize = 0;
        let cssSize = 0;
        let slowResources = 0;
        
        const resourceAnalysis = {
            images: [],
            scripts: [],
            stylesheets: [],
            fonts: [],
            other: []
        };

        resources.forEach(resource => {
            const size = resource.transferSize || resource.encodedBodySize || 0;
            const loadTime = resource.responseEnd - resource.startTime;
            
            totalSize += size;
            
            // Categorize resources
            if (resource.name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) {
                imageSize += size;
                resourceAnalysis.images.push({ name: resource.name, size, loadTime });
                
                if (size > 100000) { // 100KB
                    this.issues.push({
                        type: 'large-image',
                        resource: resource.name,
                        size: size,
                        message: `Large image: ${this.formatBytes(size)} - consider optimization`,
                        impact: 'medium'
                    });
                }
            } else if (resource.name.match(/\.js$/i)) {
                jsSize += size;
                resourceAnalysis.scripts.push({ name: resource.name, size, loadTime });
                
                if (size > 200000) { // 200KB
                    this.issues.push({
                        type: 'large-script',
                        resource: resource.name,
                        size: size,
                        message: `Large JavaScript file: ${this.formatBytes(size)} - consider code splitting`,
                        impact: 'high'
                    });
                }
            } else if (resource.name.match(/\.css$/i)) {
                cssSize += size;
                resourceAnalysis.stylesheets.push({ name: resource.name, size, loadTime });
                
                if (size > 50000) { // 50KB
                    this.issues.push({
                        type: 'large-stylesheet',
                        resource: resource.name,
                        size: size,
                        message: `Large CSS file: ${this.formatBytes(size)} - consider optimization`,
                        impact: 'medium'
                    });
                }
            } else if (resource.name.match(/\.(woff|woff2|ttf|otf)$/i)) {
                resourceAnalysis.fonts.push({ name: resource.name, size, loadTime });
            } else {
                resourceAnalysis.other.push({ name: resource.name, size, loadTime });
            }
            
            // Check for slow loading resources
            if (loadTime > 1000) { // 1 second
                slowResources++;
                this.issues.push({
                    type: 'slow-resource',
                    resource: resource.name,
                    loadTime: loadTime,
                    message: `Slow loading resource: ${loadTime.toFixed(0)}ms`,
                    impact: 'medium'
                });
            }
        });

        // Store metrics
        this.metrics.totalSize = totalSize;
        this.metrics.imageSize = imageSize;
        this.metrics.jsSize = jsSize;
        this.metrics.cssSize = cssSize;
        this.metrics.resourceCount = resources.length;
        this.metrics.resourceAnalysis = resourceAnalysis;

        // Validate against thresholds
        if (totalSize > this.thresholds.totalSize) {
            this.issues.push({
                type: 'large-page-size',
                metric: 'totalSize',
                value: totalSize,
                threshold: this.thresholds.totalSize,
                message: `Total page size is large: ${this.formatBytes(totalSize)} (target: <${this.formatBytes(this.thresholds.totalSize)})`,
                impact: 'high'
            });
        }

        if (imageSize > this.thresholds.imageSize) {
            this.issues.push({
                type: 'large-image-total',
                metric: 'imageSize',
                value: imageSize,
                threshold: this.thresholds.imageSize,
                message: `Total image size is large: ${this.formatBytes(imageSize)} (target: <${this.formatBytes(this.thresholds.imageSize)})`,
                impact: 'medium'
            });
        }

        if (jsSize > this.thresholds.jsSize) {
            this.issues.push({
                type: 'large-js-total',
                metric: 'jsSize',
                value: jsSize,
                threshold: this.thresholds.jsSize,
                message: `Total JavaScript size is large: ${this.formatBytes(jsSize)} (target: <${this.formatBytes(this.thresholds.jsSize)})`,
                impact: 'high'
            });
        }

        if (cssSize > this.thresholds.cssSize) {
            this.issues.push({
                type: 'large-css-total',
                metric: 'cssSize',
                value: cssSize,
                threshold: this.thresholds.cssSize,
                message: `Total CSS size is large: ${this.formatBytes(cssSize)} (target: <${this.formatBytes(this.thresholds.cssSize)})`,
                impact: 'medium'
            });
        }

        // Report good performance
        if (slowResources === 0) {
            this.passes.push({
                test: 'Resource Loading Speed',
                message: 'All resources load within acceptable time'
            });
        }
    }

    testImageOptimization() {
        const images = document.querySelectorAll('img');
        let unoptimizedImages = 0;
        let missingAlt = 0;
        let missingLazyLoading = 0;

        images.forEach((img, index) => {
            const src = img.src;
            const alt = img.alt;
            const loading = img.loading;
            const naturalWidth = img.naturalWidth;
            const naturalHeight = img.naturalHeight;
            const displayWidth = img.offsetWidth;
            const displayHeight = img.offsetHeight;

            // Check for missing alt text
            if (alt === null || alt === '') {
                missingAlt++;
            }

            // Check for lazy loading
            if (!loading || loading !== 'lazy') {
                missingLazyLoading++;
            }

            // Check for oversized images
            if (naturalWidth && naturalHeight && displayWidth && displayHeight) {
                const oversizeRatio = (naturalWidth * naturalHeight) / (displayWidth * displayHeight);
                if (oversizeRatio > 2) {
                    this.issues.push({
                        type: 'oversized-image',
                        element: `img[${index}]`,
                        message: `Image is ${oversizeRatio.toFixed(1)}x larger than display size`,
                        impact: 'medium'
                    });
                    unoptimizedImages++;
                }
            }

            // Check for modern image formats
            if (src && !src.match(/\.(webp|avif)$/i)) {
                this.optimizations.push({
                    type: 'image-format',
                    element: `img[${index}]`,
                    message: 'Consider using WebP or AVIF format for better compression',
                    impact: 'low'
                });
            }
        });

        // Report results
        if (unoptimizedImages === 0) {
            this.passes.push({
                test: 'Image Optimization',
                message: 'All images are properly sized'
            });
        }

        if (missingLazyLoading > 0) {
            this.optimizations.push({
                type: 'lazy-loading',
                message: `${missingLazyLoading} images missing lazy loading attribute`,
                impact: 'medium'
            });
        }
    }

    validateCaching() {
        if (!window.performance || !window.performance.getEntriesByType) return;
        
        const resources = window.performance.getEntriesByType('resource');
        let uncachedResources = 0;
        
        resources.forEach(resource => {
            // Check if resource was served from cache
            if (resource.transferSize > 0 && resource.transferSize === resource.encodedBodySize) {
                // Resource was not cached
                if (resource.name.match(/\.(js|css|jpg|jpeg|png|gif|webp|svg|woff|woff2)$/i)) {
                    uncachedResources++;
                }
            }
        });

        if (uncachedResources > 0) {
            this.optimizations.push({
                type: 'caching',
                message: `${uncachedResources} static resources not cached - implement cache headers`,
                impact: 'high'
            });
        } else {
            this.passes.push({
                test: 'Resource Caching',
                message: 'Static resources are properly cached'
            });
        }
    }

    checkJavaScriptPerformance() {
        // Check for render-blocking scripts
        const scripts = document.querySelectorAll('script[src]:not([async]):not([defer])');
        if (scripts.length > 0) {
            this.issues.push({
                type: 'render-blocking-js',
                count: scripts.length,
                message: `${scripts.length} render-blocking JavaScript files found`,
                impact: 'high'
            });
        }

        // Check for inline scripts
        const inlineScripts = document.querySelectorAll('script:not([src])');
        if (inlineScripts.length > 5) {
            this.optimizations.push({
                type: 'inline-scripts',
                count: inlineScripts.length,
                message: `${inlineScripts.length} inline scripts found - consider bundling`,
                impact: 'medium'
            });
        }

        // Check for unused JavaScript (simplified)
        const scriptTags = document.querySelectorAll('script[src]');
        if (scriptTags.length > 10) {
            this.optimizations.push({
                type: 'script-count',
                count: scriptTags.length,
                message: `${scriptTags.length} script files loaded - consider bundling`,
                impact: 'medium'
            });
        }

        // Test JavaScript execution time
        const startTime = performance.now();
        
        // Simulate some work
        for (let i = 0; i < 1000; i++) {
            document.querySelector('body');
        }
        
        const executionTime = performance.now() - startTime;
        
        if (executionTime > 16) { // 16ms = 60fps
            this.issues.push({
                type: 'slow-js-execution',
                time: executionTime,
                message: `JavaScript execution time: ${executionTime.toFixed(2)}ms (may cause frame drops)`,
                impact: 'medium'
            });
        }
    }

    analyzeCSSPerformance() {
        // Check for render-blocking CSS
        const stylesheets = document.querySelectorAll('link[rel="stylesheet"]:not([media="print"])');
        if (stylesheets.length > 3) {
            this.optimizations.push({
                type: 'css-files',
                count: stylesheets.length,
                message: `${stylesheets.length} CSS files found - consider bundling`,
                impact: 'medium'
            });
        }

        // Check for unused CSS (simplified check)
        const allRules = [];
        try {
            for (let sheet of document.styleSheets) {
                if (sheet.cssRules) {
                    for (let rule of sheet.cssRules) {
                        if (rule.selectorText) {
                            allRules.push(rule.selectorText);
                        }
                    }
                }
            }
            
            let unusedRules = 0;
            allRules.forEach(selector => {
                try {
                    if (!document.querySelector(selector)) {
                        unusedRules++;
                    }
                } catch (e) {
                    // Invalid selector
                }
            });
            
            if (unusedRules > allRules.length * 0.3) { // More than 30% unused
                this.optimizations.push({
                    type: 'unused-css',
                    percentage: Math.round((unusedRules / allRules.length) * 100),
                    message: `Approximately ${Math.round((unusedRules / allRules.length) * 100)}% of CSS rules may be unused`,
                    impact: 'medium'
                });
            }
        } catch (error) {
            // CSS analysis failed (likely due to CORS)
            console.warn('CSS analysis failed:', error);
        }

        // Check for critical CSS inlining
        const inlineStyles = document.querySelectorAll('style');
        if (inlineStyles.length === 0) {
            this.optimizations.push({
                type: 'critical-css',
                message: 'Consider inlining critical CSS for faster rendering',
                impact: 'medium'
            });
        }
    }

    testMobilePerformance() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile || window.innerWidth <= 768) {
            // Check viewport meta tag
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            if (!viewportMeta) {
                this.issues.push({
                    type: 'missing-viewport',
                    message: 'Missing viewport meta tag for mobile optimization',
                    impact: 'high'
                });
            }

            // Check for touch-friendly elements
            const buttons = document.querySelectorAll('button, a, input');
            let smallTouchTargets = 0;
            
            buttons.forEach(button => {
                const rect = button.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44)) {
                    smallTouchTargets++;
                }
            });

            if (smallTouchTargets > 0) {
                this.issues.push({
                    type: 'small-touch-targets',
                    count: smallTouchTargets,
                    message: `${smallTouchTargets} touch targets smaller than 44px`,
                    impact: 'medium'
                });
            }

            // Check for mobile-specific optimizations
            if (this.metrics.totalSize > 1000000) { // 1MB
                this.issues.push({
                    type: 'mobile-page-size',
                    size: this.metrics.totalSize,
                    message: `Page size too large for mobile: ${this.formatBytes(this.metrics.totalSize)}`,
                    impact: 'high'
                });
            }
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    generatePerformanceReport() {
        const totalIssues = this.issues.length;
        const highImpactIssues = this.issues.filter(i => i.impact === 'high').length;
        const mediumImpactIssues = this.issues.filter(i => i.impact === 'medium').length;
        const lowImpactIssues = this.issues.filter(i => i.impact === 'low').length;

        // Calculate performance score (simplified)
        let score = 100;
        score -= highImpactIssues * 15;
        score -= mediumImpactIssues * 10;
        score -= lowImpactIssues * 5;
        score = Math.max(0, score);

        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                performanceScore: score,
                totalIssues: totalIssues,
                highImpactIssues: highImpactIssues,
                mediumImpactIssues: mediumImpactIssues,
                lowImpactIssues: lowImpactIssues,
                optimizations: this.optimizations.length,
                passes: this.passes.length,
                meetsThresholds: score >= this.thresholds.performanceScore
            },
            metrics: this.metrics,
            issues: this.issues,
            optimizations: this.optimizations,
            passes: this.passes,
            recommendations: this.generateRecommendations()
        };

        this.displayPerformanceReport(report);
        window.performanceReport = report;
        
        // Dispatch event for external listeners
        window.dispatchEvent(new CustomEvent('performanceTestComplete', { detail: report }));
    }

    generateRecommendations() {
        const recommendations = [];

        // High impact recommendations
        const highImpactIssues = this.issues.filter(i => i.impact === 'high');
        if (highImpactIssues.length > 0) {
            recommendations.push({
                priority: 'high',
                category: 'Critical Performance Issues',
                items: highImpactIssues.map(issue => issue.message)
            });
        }

        // Optimization recommendations
        if (this.optimizations.length > 0) {
            recommendations.push({
                priority: 'medium',
                category: 'Performance Optimizations',
                items: this.optimizations.map(opt => opt.message)
            });
        }

        // Core Web Vitals recommendations
        if (this.metrics.LCP > this.thresholds.LCP) {
            recommendations.push({
                priority: 'high',
                category: 'Largest Contentful Paint',
                items: [
                    'Optimize images and use modern formats (WebP, AVIF)',
                    'Implement lazy loading for images',
                    'Minimize render-blocking resources',
                    'Use a CDN for faster content delivery'
                ]
            });
        }

        if (this.metrics.CLS > this.thresholds.CLS) {
            recommendations.push({
                priority: 'high',
                category: 'Cumulative Layout Shift',
                items: [
                    'Set explicit dimensions for images and videos',
                    'Reserve space for dynamic content',
                    'Avoid inserting content above existing content',
                    'Use CSS aspect-ratio for responsive media'
                ]
            });
        }

        return recommendations;
    }

    displayPerformanceReport(report) {
        console.log('=== PERFORMANCE VALIDATION REPORT ===');
        console.log(`Performance Score: ${report.summary.performanceScore}/100`);
        console.log(`Meets Thresholds: ${report.summary.meetsThresholds ? 'Yes' : 'No'}`);
        console.log(`Issues: ${report.summary.totalIssues} (High: ${report.summary.highImpactIssues}, Medium: ${report.summary.mediumImpactIssues}, Low: ${report.summary.lowImpactIssues})`);
        console.log(`Optimizations: ${report.summary.optimizations} | Passes: ${report.summary.passes}`);
        console.log('');

        // Core Web Vitals
        if (Object.keys(this.metrics).length > 0) {
            console.log('CORE WEB VITALS:');
            if (this.metrics.LCP) console.log(`LCP: ${this.metrics.LCP.toFixed(0)}ms (target: <${this.thresholds.LCP}ms)`);
            if (this.metrics.FID) console.log(`FID: ${this.metrics.FID.toFixed(0)}ms (target: <${this.thresholds.FID}ms)`);
            if (this.metrics.CLS) console.log(`CLS: ${this.metrics.CLS.toFixed(3)} (target: <${this.thresholds.CLS})`);
            console.log('');
        }

        // Resource metrics
        if (this.metrics.totalSize) {
            console.log('RESOURCE ANALYSIS:');
            console.log(`Total Size: ${this.formatBytes(this.metrics.totalSize)}`);
            console.log(`Images: ${this.formatBytes(this.metrics.imageSize)}`);
            console.log(`JavaScript: ${this.formatBytes(this.metrics.jsSize)}`);
            console.log(`CSS: ${this.formatBytes(this.metrics.cssSize)}`);
            console.log(`Resources: ${this.metrics.resourceCount}`);
            console.log('');
        }

        // Issues
        if (report.summary.totalIssues > 0) {
            console.log('PERFORMANCE ISSUES:');
            this.issues.forEach(issue => {
                const icon = issue.impact === 'high' ? '🚨' : issue.impact === 'medium' ? '⚠️' : 'ℹ️';
                console.log(`${icon} ${issue.message}`);
            });
            console.log('');
        }

        // Optimizations
        if (report.summary.optimizations > 0) {
            console.log('OPTIMIZATION OPPORTUNITIES:');
            this.optimizations.forEach(opt => {
                console.log(`💡 ${opt.message}`);
            });
            console.log('');
        }

        // Passes
        if (report.summary.passes > 0) {
            console.log('PERFORMANCE PASSES:');
            this.passes.forEach(pass => {
                console.log(`✅ ${pass.test}: ${pass.message}`);
            });
            console.log('');
        }

        // Recommendations
        if (report.recommendations.length > 0) {
            console.log('RECOMMENDATIONS:');
            report.recommendations.forEach(rec => {
                console.log(`${rec.priority.toUpperCase()}: ${rec.category}`);
                rec.items.forEach(item => {
                    console.log(`  - ${item}`);
                });
            });
        }

        // Overall assessment
        if (report.summary.performanceScore >= 90) {
            console.log('🎉 Excellent performance! Dashboard is well optimized.');
        } else if (report.summary.performanceScore >= 70) {
            console.log('👍 Good performance with room for improvement.');
        } else {
            console.log('⚠️ Performance needs attention. Focus on high-impact issues first.');
        }
    }
}

// Auto-run performance validation
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait a bit for resources to load
        setTimeout(() => {
            new PerformanceValidator();
        }, 2000);
    });
} else {
    setTimeout(() => {
        new PerformanceValidator();
    }, 2000);
}

// Export for manual testing
window.PerformanceValidator = PerformanceValidator;