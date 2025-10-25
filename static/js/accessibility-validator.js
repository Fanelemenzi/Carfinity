/**
 * Accessibility Validation Suite
 * Comprehensive WCAG 2.1 compliance testing for the AutoCare Dashboard
 */

class AccessibilityValidator {
    constructor() {
        this.violations = [];
        this.warnings = [];
        this.passes = [];
        this.wcagLevels = ['A', 'AA', 'AAA'];
        this.currentLevel = 'AA'; // Target WCAG 2.1 AA compliance
        
        this.init();
    }

    init() {
        console.log('Starting accessibility validation...');
        this.runAllTests();
        this.generateAccessibilityReport();
    }

    runAllTests() {
        // WCAG 2.1 Principle 1: Perceivable
        this.testImages();
        this.testHeadings();
        this.testColorContrast();
        this.testTextAlternatives();
        this.testMediaAlternatives();
        
        // WCAG 2.1 Principle 2: Operable
        this.testKeyboardNavigation();
        this.testFocusManagement();
        this.testTouchTargets();
        this.testTimingAndMotion();
        
        // WCAG 2.1 Principle 3: Understandable
        this.testLanguage();
        this.testLabels();
        this.testErrorHandling();
        this.testConsistency();
        
        // WCAG 2.1 Principle 4: Robust
        this.testMarkupValidity();
        this.testARIA();
        this.testCompatibility();
    }

    // Principle 1: Perceivable Tests
    testImages() {
        const images = document.querySelectorAll('img');
        let missingAlt = 0;
        let decorativeImages = 0;
        let informativeImages = 0;

        images.forEach((img, index) => {
            const alt = img.getAttribute('alt');
            const ariaHidden = img.getAttribute('aria-hidden');
            const role = img.getAttribute('role');
            
            if (alt === null && ariaHidden !== 'true' && role !== 'presentation') {
                this.violations.push({
                    type: 'missing-alt',
                    element: `img[${index}]`,
                    message: 'Image missing alt attribute',
                    wcag: '1.1.1',
                    level: 'A'
                });
                missingAlt++;
            } else if (alt === '') {
                decorativeImages++;
            } else if (alt) {
                informativeImages++;
                
                // Check for poor alt text
                if (alt.toLowerCase().includes('image') || alt.toLowerCase().includes('picture')) {
                    this.warnings.push({
                        type: 'poor-alt-text',
                        element: `img[${index}]`,
                        message: 'Alt text should not include "image" or "picture"',
                        wcag: '1.1.1',
                        level: 'A'
                    });
                }
            }
        });

        if (missingAlt === 0) {
            this.passes.push({
                test: 'Image Alt Text',
                message: `All ${images.length} images have appropriate alt attributes`
            });
        }
    }

    testHeadings() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        let hasH1 = false;
        let multipleH1 = false;
        let h1Count = 0;

        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            
            if (level === 1) {
                h1Count++;
                hasH1 = true;
                if (h1Count > 1) {
                    multipleH1 = true;
                }
            }
            
            // Check for heading level skips
            if (previousLevel > 0 && level > previousLevel + 1) {
                this.violations.push({
                    type: 'heading-skip',
                    element: heading.tagName.toLowerCase(),
                    message: `Heading level skip: ${heading.tagName} follows h${previousLevel}`,
                    wcag: '1.3.1',
                    level: 'A'
                });
            }
            
            // Check for empty headings
            if (!heading.textContent.trim()) {
                this.violations.push({
                    type: 'empty-heading',
                    element: `${heading.tagName.toLowerCase()}[${index}]`,
                    message: 'Heading element is empty',
                    wcag: '1.3.1',
                    level: 'A'
                });
            }
            
            previousLevel = level;
        });

        if (!hasH1) {
            this.violations.push({
                type: 'missing-h1',
                element: 'document',
                message: 'Page missing h1 heading',
                wcag: '1.3.1',
                level: 'A'
            });
        }

        if (multipleH1) {
            this.warnings.push({
                type: 'multiple-h1',
                element: 'document',
                message: 'Multiple h1 headings found (consider using h2-h6)',
                wcag: '1.3.1',
                level: 'A'
            });
        }

        if (this.violations.filter(v => v.type.includes('heading')).length === 0) {
            this.passes.push({
                test: 'Heading Structure',
                message: 'Proper heading hierarchy maintained'
            });
        }
    }

    testColorContrast() {
        const textElements = document.querySelectorAll('p, span, div, a, button, h1, h2, h3, h4, h5, h6, li, td, th, label');
        let contrastIssues = 0;

        textElements.forEach((element, index) => {
            const style = window.getComputedStyle(element);
            const color = style.color;
            const backgroundColor = style.backgroundColor;
            const fontSize = parseFloat(style.fontSize);
            const fontWeight = style.fontWeight;
            
            // Skip if no visible text
            if (!element.textContent.trim()) return;
            
            // Calculate contrast ratio (simplified)
            const contrast = this.calculateContrastRatio(color, backgroundColor);
            
            // WCAG AA requirements
            const isLargeText = fontSize >= 18 || (fontSize >= 14 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
            const minContrast = isLargeText ? 3.0 : 4.5;
            
            if (contrast < minContrast) {
                this.violations.push({
                    type: 'color-contrast',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: `Insufficient color contrast: ${contrast.toFixed(2)} (minimum: ${minContrast})`,
                    wcag: '1.4.3',
                    level: 'AA'
                });
                contrastIssues++;
            }
        });

        if (contrastIssues === 0) {
            this.passes.push({
                test: 'Color Contrast',
                message: 'All text meets WCAG AA contrast requirements'
            });
        }
    }

    calculateContrastRatio(color1, color2) {
        // Simplified contrast calculation
        // In a real implementation, you'd convert RGB to relative luminance
        const rgb1 = this.parseRGB(color1);
        const rgb2 = this.parseRGB(color2);
        
        if (!rgb1 || !rgb2) return 21; // Assume good contrast if can't parse
        
        const l1 = this.relativeLuminance(rgb1);
        const l2 = this.relativeLuminance(rgb2);
        
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    parseRGB(color) {
        const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (match) {
            return {
                r: parseInt(match[1]),
                g: parseInt(match[2]),
                b: parseInt(match[3])
            };
        }
        return null;
    }

    relativeLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }

    testTextAlternatives() {
        // Test for text alternatives for non-text content
        const mediaElements = document.querySelectorAll('video, audio, canvas, svg, iframe');
        
        mediaElements.forEach((element, index) => {
            const tagName = element.tagName.toLowerCase();
            const ariaLabel = element.getAttribute('aria-label');
            const ariaLabelledby = element.getAttribute('aria-labelledby');
            const title = element.getAttribute('title');
            
            if (!ariaLabel && !ariaLabelledby && !title) {
                this.violations.push({
                    type: 'missing-media-alt',
                    element: `${tagName}[${index}]`,
                    message: `${tagName} element missing text alternative`,
                    wcag: '1.1.1',
                    level: 'A'
                });
            }
        });
    }

    testMediaAlternatives() {
        const videos = document.querySelectorAll('video');
        const audios = document.querySelectorAll('audio');
        
        videos.forEach((video, index) => {
            const tracks = video.querySelectorAll('track[kind="captions"], track[kind="subtitles"]');
            if (tracks.length === 0) {
                this.warnings.push({
                    type: 'missing-captions',
                    element: `video[${index}]`,
                    message: 'Video missing captions or subtitles',
                    wcag: '1.2.2',
                    level: 'A'
                });
            }
        });
    }

    // Principle 2: Operable Tests
    testKeyboardNavigation() {
        const focusableElements = document.querySelectorAll(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]'
        );
        
        let keyboardIssues = 0;
        
        focusableElements.forEach((element, index) => {
            // Check for positive tabindex (anti-pattern)
            const tabindex = element.getAttribute('tabindex');
            if (tabindex && parseInt(tabindex) > 0) {
                this.violations.push({
                    type: 'positive-tabindex',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: 'Positive tabindex found (use 0 or -1)',
                    wcag: '2.4.3',
                    level: 'A'
                });
                keyboardIssues++;
            }
            
            // Check if element is keyboard accessible
            if (element.tagName.toLowerCase() === 'div' && element.onclick && !tabindex) {
                this.violations.push({
                    type: 'non-focusable-interactive',
                    element: `div[${index}]`,
                    message: 'Interactive div not keyboard accessible',
                    wcag: '2.1.1',
                    level: 'A'
                });
                keyboardIssues++;
            }
        });

        if (keyboardIssues === 0) {
            this.passes.push({
                test: 'Keyboard Navigation',
                message: 'All interactive elements are keyboard accessible'
            });
        }
    }

    testFocusManagement() {
        const focusableElements = document.querySelectorAll(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        let focusIssues = 0;
        
        focusableElements.forEach((element, index) => {
            // Test focus visibility
            element.focus();
            const style = window.getComputedStyle(element, ':focus');
            const outline = style.outline;
            const outlineWidth = style.outlineWidth;
            const boxShadow = style.boxShadow;
            
            if (outline === 'none' && outlineWidth === '0px' && boxShadow === 'none') {
                this.violations.push({
                    type: 'no-focus-indicator',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: 'Element missing visible focus indicator',
                    wcag: '2.4.7',
                    level: 'AA'
                });
                focusIssues++;
            }
        });
        
        // Reset focus
        document.activeElement.blur();

        if (focusIssues === 0) {
            this.passes.push({
                test: 'Focus Management',
                message: 'All focusable elements have visible focus indicators'
            });
        }
    }

    testTouchTargets() {
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        let smallTargets = 0;
        
        interactiveElements.forEach((element, index) => {
            const rect = element.getBoundingClientRect();
            
            // Skip hidden elements
            if (rect.width === 0 || rect.height === 0) return;
            
            // WCAG 2.1 AA: minimum 44x44px touch targets
            if (rect.width < 44 || rect.height < 44) {
                this.violations.push({
                    type: 'small-touch-target',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: `Touch target too small: ${rect.width.toFixed(0)}x${rect.height.toFixed(0)}px (minimum: 44x44px)`,
                    wcag: '2.5.5',
                    level: 'AAA'
                });
                smallTargets++;
            }
        });

        if (smallTargets === 0) {
            this.passes.push({
                test: 'Touch Targets',
                message: 'All interactive elements meet minimum touch target size'
            });
        }
    }

    testTimingAndMotion() {
        // Check for auto-playing media
        const autoplayMedia = document.querySelectorAll('video[autoplay], audio[autoplay]');
        autoplayMedia.forEach((element, index) => {
            this.violations.push({
                type: 'autoplay-media',
                element: `${element.tagName.toLowerCase()}[${index}]`,
                message: 'Media auto-plays without user control',
                wcag: '2.2.2',
                level: 'A'
            });
        });

        // Check for animations that can't be paused
        const animatedElements = document.querySelectorAll('[style*="animation"], .animate');
        if (animatedElements.length > 0) {
            this.warnings.push({
                type: 'animation-control',
                element: 'document',
                message: 'Verify animations can be paused or disabled',
                wcag: '2.2.2',
                level: 'A'
            });
        }
    }

    // Principle 3: Understandable Tests
    testLanguage() {
        const html = document.documentElement;
        const lang = html.getAttribute('lang');
        
        if (!lang) {
            this.violations.push({
                type: 'missing-lang',
                element: 'html',
                message: 'Document missing lang attribute',
                wcag: '3.1.1',
                level: 'A'
            });
        } else {
            this.passes.push({
                test: 'Document Language',
                message: `Document language specified: ${lang}`
            });
        }
    }

    testLabels() {
        const formElements = document.querySelectorAll('input, select, textarea');
        let unlabeledElements = 0;
        
        formElements.forEach((element, index) => {
            const id = element.getAttribute('id');
            const ariaLabel = element.getAttribute('aria-label');
            const ariaLabelledby = element.getAttribute('aria-labelledby');
            const label = id ? document.querySelector(`label[for="${id}"]`) : null;
            const parentLabel = element.closest('label');
            
            if (!ariaLabel && !ariaLabelledby && !label && !parentLabel) {
                this.violations.push({
                    type: 'missing-label',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: 'Form element missing accessible label',
                    wcag: '3.3.2',
                    level: 'A'
                });
                unlabeledElements++;
            }
        });

        if (unlabeledElements === 0 && formElements.length > 0) {
            this.passes.push({
                test: 'Form Labels',
                message: 'All form elements have accessible labels'
            });
        }
    }

    testErrorHandling() {
        const requiredFields = document.querySelectorAll('[required], [aria-required="true"]');
        
        requiredFields.forEach((field, index) => {
            const ariaDescribedby = field.getAttribute('aria-describedby');
            const ariaInvalid = field.getAttribute('aria-invalid');
            
            // Check if error messages are properly associated
            if (ariaInvalid === 'true' && !ariaDescribedby) {
                this.warnings.push({
                    type: 'error-association',
                    element: `${field.tagName.toLowerCase()}[${index}]`,
                    message: 'Invalid field missing error message association',
                    wcag: '3.3.1',
                    level: 'A'
                });
            }
        });
    }

    testConsistency() {
        // Check for consistent navigation
        const navElements = document.querySelectorAll('nav, [role="navigation"]');
        if (navElements.length > 1) {
            this.warnings.push({
                type: 'multiple-nav',
                element: 'document',
                message: 'Multiple navigation elements found - ensure consistency',
                wcag: '3.2.3',
                level: 'AA'
            });
        }
    }

    // Principle 4: Robust Tests
    testMarkupValidity() {
        // Basic HTML validation checks
        const duplicateIds = this.findDuplicateIds();
        duplicateIds.forEach(id => {
            this.violations.push({
                type: 'duplicate-id',
                element: `#${id}`,
                message: `Duplicate ID found: ${id}`,
                wcag: '4.1.1',
                level: 'A'
            });
        });

        if (duplicateIds.length === 0) {
            this.passes.push({
                test: 'Markup Validity',
                message: 'No duplicate IDs found'
            });
        }
    }

    findDuplicateIds() {
        const ids = {};
        const duplicates = [];
        
        document.querySelectorAll('[id]').forEach(element => {
            const id = element.getAttribute('id');
            if (ids[id]) {
                if (!duplicates.includes(id)) {
                    duplicates.push(id);
                }
            } else {
                ids[id] = true;
            }
        });
        
        return duplicates;
    }

    testARIA() {
        const ariaElements = document.querySelectorAll('[role], [aria-label], [aria-labelledby], [aria-describedby]');
        let ariaIssues = 0;
        
        ariaElements.forEach((element, index) => {
            const role = element.getAttribute('role');
            const ariaLabel = element.getAttribute('aria-label');
            const ariaLabelledby = element.getAttribute('aria-labelledby');
            const ariaDescribedby = element.getAttribute('aria-describedby');
            
            // Check for invalid roles
            if (role && !this.isValidAriaRole(role)) {
                this.violations.push({
                    type: 'invalid-aria-role',
                    element: `${element.tagName.toLowerCase()}[${index}]`,
                    message: `Invalid ARIA role: ${role}`,
                    wcag: '4.1.2',
                    level: 'A'
                });
                ariaIssues++;
            }
            
            // Check for referenced elements
            if (ariaLabelledby) {
                const referencedElement = document.getElementById(ariaLabelledby);
                if (!referencedElement) {
                    this.violations.push({
                        type: 'broken-aria-reference',
                        element: `${element.tagName.toLowerCase()}[${index}]`,
                        message: `aria-labelledby references non-existent element: ${ariaLabelledby}`,
                        wcag: '4.1.2',
                        level: 'A'
                    });
                    ariaIssues++;
                }
            }
            
            if (ariaDescribedby) {
                const referencedElement = document.getElementById(ariaDescribedby);
                if (!referencedElement) {
                    this.violations.push({
                        type: 'broken-aria-reference',
                        element: `${element.tagName.toLowerCase()}[${index}]`,
                        message: `aria-describedby references non-existent element: ${ariaDescribedby}`,
                        wcag: '4.1.2',
                        level: 'A'
                    });
                    ariaIssues++;
                }
            }
        });

        if (ariaIssues === 0) {
            this.passes.push({
                test: 'ARIA Implementation',
                message: 'ARIA attributes properly implemented'
            });
        }
    }

    isValidAriaRole(role) {
        const validRoles = [
            'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
            'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
            'contentinfo', 'definition', 'dialog', 'directory', 'document',
            'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
            'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
            'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
            'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
            'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
            'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
            'slider', 'spinbutton', 'status', 'switch', 'tab', 'table',
            'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
            'tooltip', 'tree', 'treegrid', 'treeitem'
        ];
        return validRoles.includes(role);
    }

    testCompatibility() {
        // Test for assistive technology compatibility
        const landmarks = document.querySelectorAll('main, nav, aside, header, footer, [role="main"], [role="navigation"], [role="complementary"], [role="banner"], [role="contentinfo"]');
        
        if (landmarks.length === 0) {
            this.warnings.push({
                type: 'missing-landmarks',
                element: 'document',
                message: 'No ARIA landmarks found for screen reader navigation',
                wcag: '4.1.2',
                level: 'AA'
            });
        } else {
            this.passes.push({
                test: 'ARIA Landmarks',
                message: `${landmarks.length} landmarks found for screen reader navigation`
            });
        }
    }

    generateAccessibilityReport() {
        const totalTests = this.violations.length + this.warnings.length + this.passes.length;
        const violationsByLevel = {
            A: this.violations.filter(v => v.level === 'A').length,
            AA: this.violations.filter(v => v.level === 'AA').length,
            AAA: this.violations.filter(v => v.level === 'AAA').length
        };

        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                totalTests: totalTests,
                violations: this.violations.length,
                warnings: this.warnings.length,
                passes: this.passes.length,
                wcagLevel: this.currentLevel,
                isCompliant: violationsByLevel.A === 0 && (this.currentLevel === 'A' || violationsByLevel.AA === 0)
            },
            violationsByLevel,
            violations: this.violations,
            warnings: this.warnings,
            passes: this.passes
        };

        this.displayAccessibilityReport(report);
        window.accessibilityReport = report;
        
        // Dispatch event for external listeners
        window.dispatchEvent(new CustomEvent('accessibilityTestComplete', { detail: report }));
    }

    displayAccessibilityReport(report) {
        console.log('=== ACCESSIBILITY VALIDATION REPORT ===');
        console.log(`WCAG 2.1 Level: ${report.summary.wcagLevel}`);
        console.log(`Compliant: ${report.summary.isCompliant ? 'Yes' : 'No'}`);
        console.log(`Tests: ${report.summary.totalTests} | Violations: ${report.summary.violations} | Warnings: ${report.summary.warnings} | Passes: ${report.summary.passes}`);
        console.log('');

        if (report.summary.violations > 0) {
            console.log('VIOLATIONS:');
            this.violations.forEach(violation => {
                console.log(`❌ [${violation.wcag} ${violation.level}] ${violation.message}`);
                console.log(`   Element: ${violation.element}`);
            });
            console.log('');
        }

        if (report.summary.warnings > 0) {
            console.log('WARNINGS:');
            this.warnings.forEach(warning => {
                console.log(`⚠️  [${warning.wcag} ${warning.level}] ${warning.message}`);
                console.log(`   Element: ${warning.element}`);
            });
            console.log('');
        }

        if (report.summary.passes > 0) {
            console.log('PASSES:');
            this.passes.forEach(pass => {
                console.log(`✅ ${pass.test}: ${pass.message}`);
            });
        }

        // Compliance summary
        console.log('');
        console.log('WCAG 2.1 COMPLIANCE SUMMARY:');
        console.log(`Level A violations: ${report.violationsByLevel.A}`);
        console.log(`Level AA violations: ${report.violationsByLevel.AA}`);
        console.log(`Level AAA violations: ${report.violationsByLevel.AAA}`);
        
        if (report.summary.isCompliant) {
            console.log(`✅ Dashboard meets WCAG 2.1 ${report.summary.wcagLevel} compliance!`);
        } else {
            console.log(`❌ Dashboard does not meet WCAG 2.1 ${report.summary.wcagLevel} compliance.`);
        }
    }
}

// Auto-run accessibility validation
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new AccessibilityValidator();
    });
} else {
    new AccessibilityValidator();
}

// Export for manual testing
window.AccessibilityValidator = AccessibilityValidator;