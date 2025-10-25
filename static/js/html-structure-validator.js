/**
 * HTML Structure and Semantic Markup Validator
 * Validates HTML5 semantic structure and best practices
 */

class HTMLStructureValidator {
    constructor() {
        this.violations = [];
        this.warnings = [];
        this.passes = [];
        this.semanticElements = [
            'header', 'nav', 'main', 'article', 'section', 'aside', 'footer',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li',
            'figure', 'figcaption', 'blockquote', 'cite', 'time', 'address'
        ];
        
        this.init();
    }

    init() {
        console.log('Starting HTML structure validation...');
        this.validateDocumentStructure();
        this.validateSemanticMarkup();
        this.validateHeadingStructure();
        this.validateListStructure();
        this.validateTableStructure();
        this.validateFormStructure();
        this.validateLinkStructure();
        this.validateMediaElements();
        this.validateMetadata();
        this.generateStructureReport();
    }

    validateDocumentStructure() {
        // Check for required HTML5 structure
        const doctype = document.doctype;
        if (!doctype || doctype.name !== 'html') {
            this.violations.push({
                type: 'missing-doctype',
                element: 'document',
                message: 'Missing or incorrect HTML5 doctype declaration',
                severity: 'high'
            });
        } else {
            this.passes.push({
                test: 'HTML5 Doctype',
                message: 'Correct HTML5 doctype declaration found'
            });
        }

        // Check for lang attribute
        const html = document.documentElement;
        const lang = html.getAttribute('lang');
        if (!lang) {
            this.violations.push({
                type: 'missing-lang',
                element: 'html',
                message: 'Missing lang attribute on html element',
                severity: 'high'
            });
        } else {
            this.passes.push({
                test: 'Document Language',
                message: `Document language specified: ${lang}`
            });
        }

        // Check for essential landmarks
        const landmarks = {
            header: document.querySelector('header, [role="banner"]'),
            nav: document.querySelector('nav, [role="navigation"]'),
            main: document.querySelector('main, [role="main"]'),
            footer: document.querySelector('footer, [role="contentinfo"]')
        };

        Object.entries(landmarks).forEach(([landmark, element]) => {
            if (!element) {
                this.violations.push({
                    type: 'missing-landmark',
                    element: landmark,
                    message: `Missing ${landmark} landmark element`,
                    severity: 'medium'
                });
            } else {
                this.passes.push({
                    test: `${landmark.charAt(0).toUpperCase() + landmark.slice(1)} Landmark`,
                    message: `${landmark} landmark properly implemented`
                });
            }
        });

        // Check for multiple main elements
        const mainElements = document.querySelectorAll('main, [role="main"]');
        if (mainElements.length > 1) {
            this.violations.push({
                type: 'multiple-main',
                element: 'main',
                message: 'Multiple main elements found (should be only one)',
                severity: 'high'
            });
        }
    }

    validateSemanticMarkup() {
        // Check for proper use of semantic elements
        const divs = document.querySelectorAll('div');
        let semanticIssues = 0;

        divs.forEach((div, index) => {
            const className = div.className;
            const id = div.id;
            
            // Check for divs that should be semantic elements
            if (className.includes('header') || id.includes('header')) {
                this.warnings.push({
                    type: 'semantic-opportunity',
                    element: `div[${index}]`,
                    message: 'Consider using <header> instead of div with header class/id',
                    severity: 'low'
                });
                semanticIssues++;
            }
            
            if (className.includes('nav') || id.includes('nav')) {
                this.warnings.push({
                    type: 'semantic-opportunity',
                    element: `div[${index}]`,
                    message: 'Consider using <nav> instead of div with nav class/id',
                    severity: 'low'
                });
                semanticIssues++;
            }
            
            if (className.includes('main') || id.includes('main')) {
                this.warnings.push({
                    type: 'semantic-opportunity',
                    element: `div[${index}]`,
                    message: 'Consider using <main> instead of div with main class/id',
                    severity: 'low'
                });
                semanticIssues++;
            }
            
            if (className.includes('footer') || id.includes('footer')) {
                this.warnings.push({
                    type: 'semantic-opportunity',
                    element: `div[${index}]`,
                    message: 'Consider using <footer> instead of div with footer class/id',
                    severity: 'low'
                });
                semanticIssues++;
            }
        });

        // Check for proper article/section usage
        const articles = document.querySelectorAll('article');
        const sections = document.querySelectorAll('section');
        
        articles.forEach((article, index) => {
            const heading = article.querySelector('h1, h2, h3, h4, h5, h6');
            if (!heading) {
                this.warnings.push({
                    type: 'article-no-heading',
                    element: `article[${index}]`,
                    message: 'Article element should contain a heading',
                    severity: 'medium'
                });
            }
        });

        sections.forEach((section, index) => {
            const heading = section.querySelector('h1, h2, h3, h4, h5, h6');
            if (!heading) {
                this.warnings.push({
                    type: 'section-no-heading',
                    element: `section[${index}]`,
                    message: 'Section element should contain a heading',
                    severity: 'medium'
                });
            }
        });

        if (semanticIssues === 0) {
            this.passes.push({
                test: 'Semantic Markup',
                message: 'Good use of semantic HTML elements'
            });
        }
    }

    validateHeadingStructure() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        let hasH1 = false;
        let multipleH1 = false;
        let h1Count = 0;
        let emptyHeadings = 0;

        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            const text = heading.textContent.trim();
            
            // Track H1 usage
            if (level === 1) {
                h1Count++;
                hasH1 = true;
                if (h1Count > 1) {
                    multipleH1 = true;
                }
            }
            
            // Check for empty headings
            if (!text) {
                this.violations.push({
                    type: 'empty-heading',
                    element: `${heading.tagName.toLowerCase()}[${index}]`,
                    message: 'Heading element is empty',
                    severity: 'high'
                });
                emptyHeadings++;
            }
            
            // Check for heading level skips
            if (previousLevel > 0 && level > previousLevel + 1) {
                this.violations.push({
                    type: 'heading-skip',
                    element: `${heading.tagName.toLowerCase()}[${index}]`,
                    message: `Heading level skip: ${heading.tagName} follows h${previousLevel}`,
                    severity: 'medium'
                });
            }
            
            // Check for very long headings
            if (text.length > 100) {
                this.warnings.push({
                    type: 'long-heading',
                    element: `${heading.tagName.toLowerCase()}[${index}]`,
                    message: `Heading text is very long (${text.length} characters)`,
                    severity: 'low'
                });
            }
            
            previousLevel = level;
        });

        // Validate H1 usage
        if (!hasH1) {
            this.violations.push({
                type: 'missing-h1',
                element: 'document',
                message: 'Page missing h1 heading',
                severity: 'high'
            });
        }

        if (multipleH1) {
            this.warnings.push({
                type: 'multiple-h1',
                element: 'document',
                message: 'Multiple h1 headings found (consider using h2-h6)',
                severity: 'medium'
            });
        }

        if (emptyHeadings === 0 && hasH1 && !multipleH1) {
            this.passes.push({
                test: 'Heading Structure',
                message: 'Proper heading hierarchy and structure'
            });
        }
    }

    validateListStructure() {
        const lists = document.querySelectorAll('ul, ol');
        let listIssues = 0;

        lists.forEach((list, index) => {
            const listItems = list.children;
            let hasNonLiChildren = false;
            
            // Check if all direct children are li elements
            Array.from(listItems).forEach(child => {
                if (child.tagName.toLowerCase() !== 'li') {
                    hasNonLiChildren = true;
                }
            });
            
            if (hasNonLiChildren) {
                this.violations.push({
                    type: 'invalid-list-children',
                    element: `${list.tagName.toLowerCase()}[${index}]`,
                    message: 'List contains non-li direct children',
                    severity: 'medium'
                });
                listIssues++;
            }
            
            // Check for empty lists
            if (listItems.length === 0) {
                this.violations.push({
                    type: 'empty-list',
                    element: `${list.tagName.toLowerCase()}[${index}]`,
                    message: 'Empty list element',
                    severity: 'medium'
                });
                listIssues++;
            }
        });

        // Check for orphaned li elements
        const orphanedLis = document.querySelectorAll('li:not(ul > li):not(ol > li)');
        orphanedLis.forEach((li, index) => {
            this.violations.push({
                type: 'orphaned-li',
                element: `li[${index}]`,
                message: 'li element not inside ul or ol',
                severity: 'high'
            });
            listIssues++;
        });

        if (listIssues === 0 && lists.length > 0) {
            this.passes.push({
                test: 'List Structure',
                message: 'All lists properly structured'
            });
        }
    }

    validateTableStructure() {
        const tables = document.querySelectorAll('table');
        let tableIssues = 0;

        tables.forEach((table, index) => {
            const caption = table.querySelector('caption');
            const thead = table.querySelector('thead');
            const tbody = table.querySelector('tbody');
            const tfoot = table.querySelector('tfoot');
            const ths = table.querySelectorAll('th');
            const trs = table.querySelectorAll('tr');

            // Check for table caption
            if (!caption) {
                this.warnings.push({
                    type: 'missing-table-caption',
                    element: `table[${index}]`,
                    message: 'Table missing caption element',
                    severity: 'low'
                });
            }

            // Check for proper table structure
            if (trs.length > 0 && !thead && !tbody) {
                this.warnings.push({
                    type: 'table-structure',
                    element: `table[${index}]`,
                    message: 'Consider using thead and tbody elements',
                    severity: 'low'
                });
            }

            // Check for table headers
            if (ths.length === 0) {
                this.violations.push({
                    type: 'missing-table-headers',
                    element: `table[${index}]`,
                    message: 'Table missing th elements',
                    severity: 'medium'
                });
                tableIssues++;
            }

            // Check th scope attributes
            ths.forEach((th, thIndex) => {
                const scope = th.getAttribute('scope');
                if (!scope) {
                    this.warnings.push({
                        type: 'missing-th-scope',
                        element: `th[${thIndex}]`,
                        message: 'th element missing scope attribute',
                        severity: 'low'
                    });
                }
            });
        });

        if (tableIssues === 0 && tables.length > 0) {
            this.passes.push({
                test: 'Table Structure',
                message: 'Tables properly structured with headers'
            });
        }
    }

    validateFormStructure() {
        const forms = document.querySelectorAll('form');
        const inputs = document.querySelectorAll('input, select, textarea');
        let formIssues = 0;

        // Validate form elements
        inputs.forEach((input, index) => {
            const type = input.type;
            const id = input.id;
            const name = input.name;
            const label = id ? document.querySelector(`label[for="${id}"]`) : null;
            const parentLabel = input.closest('label');
            const ariaLabel = input.getAttribute('aria-label');
            const ariaLabelledby = input.getAttribute('aria-labelledby');

            // Check for proper labeling
            if (!label && !parentLabel && !ariaLabel && !ariaLabelledby) {
                this.violations.push({
                    type: 'missing-form-label',
                    element: `${input.tagName.toLowerCase()}[${index}]`,
                    message: 'Form element missing accessible label',
                    severity: 'high'
                });
                formIssues++;
            }

            // Check for name attributes
            if (!name && type !== 'button' && type !== 'submit' && type !== 'reset') {
                this.warnings.push({
                    type: 'missing-name-attribute',
                    element: `${input.tagName.toLowerCase()}[${index}]`,
                    message: 'Form element missing name attribute',
                    severity: 'medium'
                });
            }

            // Check for required field indicators
            if (input.hasAttribute('required')) {
                const ariaRequired = input.getAttribute('aria-required');
                if (ariaRequired !== 'true') {
                    this.warnings.push({
                        type: 'missing-aria-required',
                        element: `${input.tagName.toLowerCase()}[${index}]`,
                        message: 'Required field missing aria-required="true"',
                        severity: 'low'
                    });
                }
            }
        });

        // Validate fieldsets
        const fieldsets = document.querySelectorAll('fieldset');
        fieldsets.forEach((fieldset, index) => {
            const legend = fieldset.querySelector('legend');
            if (!legend) {
                this.violations.push({
                    type: 'missing-fieldset-legend',
                    element: `fieldset[${index}]`,
                    message: 'Fieldset missing legend element',
                    severity: 'medium'
                });
                formIssues++;
            }
        });

        if (formIssues === 0 && inputs.length > 0) {
            this.passes.push({
                test: 'Form Structure',
                message: 'Forms properly structured with labels'
            });
        }
    }

    validateLinkStructure() {
        const links = document.querySelectorAll('a');
        let linkIssues = 0;

        links.forEach((link, index) => {
            const href = link.getAttribute('href');
            const text = link.textContent.trim();
            const ariaLabel = link.getAttribute('aria-label');
            const title = link.getAttribute('title');

            // Check for empty links
            if (!text && !ariaLabel && !title) {
                this.violations.push({
                    type: 'empty-link',
                    element: `a[${index}]`,
                    message: 'Link has no accessible text',
                    severity: 'high'
                });
                linkIssues++;
            }

            // Check for generic link text
            const genericTexts = ['click here', 'read more', 'more', 'link', 'here'];
            if (genericTexts.includes(text.toLowerCase())) {
                this.warnings.push({
                    type: 'generic-link-text',
                    element: `a[${index}]`,
                    message: `Generic link text: "${text}" - consider more descriptive text`,
                    severity: 'medium'
                });
            }

            // Check for external links
            if (href && (href.startsWith('http') && !href.includes(window.location.hostname))) {
                const target = link.getAttribute('target');
                const rel = link.getAttribute('rel');
                
                if (target === '_blank' && (!rel || !rel.includes('noopener'))) {
                    this.warnings.push({
                        type: 'external-link-security',
                        element: `a[${index}]`,
                        message: 'External link missing rel="noopener" security attribute',
                        severity: 'medium'
                    });
                }
            }

            // Check for skip links
            if (href && href.startsWith('#')) {
                const targetElement = document.querySelector(href);
                if (!targetElement) {
                    this.violations.push({
                        type: 'broken-anchor-link',
                        element: `a[${index}]`,
                        message: `Anchor link points to non-existent element: ${href}`,
                        severity: 'medium'
                    });
                    linkIssues++;
                }
            }
        });

        if (linkIssues === 0) {
            this.passes.push({
                test: 'Link Structure',
                message: 'Links properly structured with descriptive text'
            });
        }
    }

    validateMediaElements() {
        const images = document.querySelectorAll('img');
        const videos = document.querySelectorAll('video');
        const audios = document.querySelectorAll('audio');
        let mediaIssues = 0;

        // Validate images
        images.forEach((img, index) => {
            const alt = img.getAttribute('alt');
            const src = img.src;

            if (alt === null) {
                this.violations.push({
                    type: 'missing-alt-attribute',
                    element: `img[${index}]`,
                    message: 'Image missing alt attribute',
                    severity: 'high'
                });
                mediaIssues++;
            }

            // Check for decorative images
            if (alt === '' && !img.getAttribute('role') && !img.getAttribute('aria-hidden')) {
                // This might be intentional for decorative images
                this.warnings.push({
                    type: 'empty-alt-text',
                    element: `img[${index}]`,
                    message: 'Image has empty alt text - ensure this is decorative',
                    severity: 'low'
                });
            }

            // Check for missing src
            if (!src) {
                this.violations.push({
                    type: 'missing-image-src',
                    element: `img[${index}]`,
                    message: 'Image missing src attribute',
                    severity: 'high'
                });
                mediaIssues++;
            }
        });

        // Validate videos
        videos.forEach((video, index) => {
            const tracks = video.querySelectorAll('track');
            const controls = video.hasAttribute('controls');
            const autoplay = video.hasAttribute('autoplay');

            if (tracks.length === 0) {
                this.warnings.push({
                    type: 'missing-video-captions',
                    element: `video[${index}]`,
                    message: 'Video missing caption tracks',
                    severity: 'medium'
                });
            }

            if (!controls && !autoplay) {
                this.warnings.push({
                    type: 'video-no-controls',
                    element: `video[${index}]`,
                    message: 'Video missing controls attribute',
                    severity: 'medium'
                });
            }
        });

        // Validate audio
        audios.forEach((audio, index) => {
            const controls = audio.hasAttribute('controls');
            const autoplay = audio.hasAttribute('autoplay');

            if (!controls && !autoplay) {
                this.warnings.push({
                    type: 'audio-no-controls',
                    element: `audio[${index}]`,
                    message: 'Audio missing controls attribute',
                    severity: 'medium'
                });
            }
        });

        if (mediaIssues === 0) {
            this.passes.push({
                test: 'Media Elements',
                message: 'Media elements properly structured with alternatives'
            });
        }
    }

    validateMetadata() {
        const head = document.head;
        const title = document.querySelector('title');
        const metaDescription = document.querySelector('meta[name="description"]');
        const metaViewport = document.querySelector('meta[name="viewport"]');
        const metaCharset = document.querySelector('meta[charset]');

        // Check for title
        if (!title || !title.textContent.trim()) {
            this.violations.push({
                type: 'missing-title',
                element: 'title',
                message: 'Missing or empty page title',
                severity: 'high'
            });
        } else {
            const titleLength = title.textContent.length;
            if (titleLength > 60) {
                this.warnings.push({
                    type: 'long-title',
                    element: 'title',
                    message: `Page title is long (${titleLength} characters) - consider shortening`,
                    severity: 'low'
                });
            }
        }

        // Check for meta description
        if (!metaDescription) {
            this.warnings.push({
                type: 'missing-meta-description',
                element: 'meta[name="description"]',
                message: 'Missing meta description',
                severity: 'medium'
            });
        } else {
            const descLength = metaDescription.getAttribute('content').length;
            if (descLength > 160) {
                this.warnings.push({
                    type: 'long-meta-description',
                    element: 'meta[name="description"]',
                    message: `Meta description is long (${descLength} characters)`,
                    severity: 'low'
                });
            }
        }

        // Check for viewport meta tag
        if (!metaViewport) {
            this.violations.push({
                type: 'missing-viewport-meta',
                element: 'meta[name="viewport"]',
                message: 'Missing viewport meta tag',
                severity: 'high'
            });
        }

        // Check for charset
        if (!metaCharset) {
            this.violations.push({
                type: 'missing-charset',
                element: 'meta[charset]',
                message: 'Missing charset declaration',
                severity: 'high'
            });
        }

        if (title && metaDescription && metaViewport && metaCharset) {
            this.passes.push({
                test: 'Document Metadata',
                message: 'Essential metadata properly configured'
            });
        }
    }

    generateStructureReport() {
        const totalIssues = this.violations.length + this.warnings.length;
        const highSeverityIssues = this.violations.filter(v => v.severity === 'high').length;
        const mediumSeverityIssues = this.violations.filter(v => v.severity === 'medium').length + 
                                   this.warnings.filter(w => w.severity === 'medium').length;
        const lowSeverityIssues = this.warnings.filter(w => w.severity === 'low').length;

        // Calculate structure score
        let score = 100;
        score -= highSeverityIssues * 15;
        score -= mediumSeverityIssues * 8;
        score -= lowSeverityIssues * 3;
        score = Math.max(0, score);

        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                structureScore: score,
                totalIssues: totalIssues,
                violations: this.violations.length,
                warnings: this.warnings.length,
                passes: this.passes.length,
                highSeverityIssues: highSeverityIssues,
                mediumSeverityIssues: mediumSeverityIssues,
                lowSeverityIssues: lowSeverityIssues,
                isValid: highSeverityIssues === 0
            },
            violations: this.violations,
            warnings: this.warnings,
            passes: this.passes
        };

        this.displayStructureReport(report);
        window.htmlStructureReport = report;
        
        // Dispatch event for external listeners
        window.dispatchEvent(new CustomEvent('htmlStructureTestComplete', { detail: report }));
    }

    displayStructureReport(report) {
        console.log('=== HTML STRUCTURE VALIDATION REPORT ===');
        console.log(`Structure Score: ${report.summary.structureScore}/100`);
        console.log(`Valid HTML: ${report.summary.isValid ? 'Yes' : 'No'}`);
        console.log(`Issues: ${report.summary.totalIssues} (High: ${report.summary.highSeverityIssues}, Medium: ${report.summary.mediumSeverityIssues}, Low: ${report.summary.lowSeverityIssues})`);
        console.log(`Violations: ${report.summary.violations} | Warnings: ${report.summary.warnings} | Passes: ${report.summary.passes}`);
        console.log('');

        if (report.summary.violations > 0) {
            console.log('VIOLATIONS:');
            this.violations.forEach(violation => {
                const icon = violation.severity === 'high' ? '🚨' : violation.severity === 'medium' ? '⚠️' : 'ℹ️';
                console.log(`${icon} ${violation.message}`);
                console.log(`   Element: ${violation.element}`);
            });
            console.log('');
        }

        if (report.summary.warnings > 0) {
            console.log('WARNINGS:');
            this.warnings.forEach(warning => {
                const icon = warning.severity === 'medium' ? '⚠️' : 'ℹ️';
                console.log(`${icon} ${warning.message}`);
                console.log(`   Element: ${warning.element}`);
            });
            console.log('');
        }

        if (report.summary.passes > 0) {
            console.log('PASSES:');
            this.passes.forEach(pass => {
                console.log(`✅ ${pass.test}: ${pass.message}`);
            });
            console.log('');
        }

        // Overall assessment
        if (report.summary.structureScore >= 95) {
            console.log('🎉 Excellent HTML structure! Well-formed semantic markup.');
        } else if (report.summary.structureScore >= 80) {
            console.log('👍 Good HTML structure with minor improvements needed.');
        } else {
            console.log('⚠️ HTML structure needs attention. Focus on high-severity issues first.');
        }
    }
}

// Auto-run HTML structure validation
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new HTMLStructureValidator();
    });
} else {
    new HTMLStructureValidator();
}

// Export for manual testing
window.HTMLStructureValidator = HTMLStructureValidator;