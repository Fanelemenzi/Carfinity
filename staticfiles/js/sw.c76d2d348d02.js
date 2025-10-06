/**
 * Service Worker for Dashboard Caching
 * Handles offline functionality and resource caching
 */

const CACHE_NAME = 'insurance-dashboard-v1';
const STATIC_CACHE = 'static-resources-v1';
const DYNAMIC_CACHE = 'dynamic-resources-v1';

// Resources to cache immediately
const STATIC_RESOURCES = [
    '/static/css/dashboard-integration.css',
    '/static/css/notifications.css',
    '/static/js/dashboard-navigation.js',
    '/static/js/dashboard-interactivity.js',
    '/static/js/notifications.js',
    '/static/js/dashboard-animations.js',
    '/static/js/performance-optimizer.js',
    'https://cdn.tailwindcss.com',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Pages to cache
const PAGES_TO_CACHE = [
    '/insurance/',
    '/insurance/assessments/',
    '/insurance/book-assessment/'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => {
                console.log('Caching static resources...');
                return cache.addAll(STATIC_RESOURCES);
            }),
            caches.open(CACHE_NAME).then(cache => {
                console.log('Caching pages...');
                return cache.addAll(PAGES_TO_CACHE);
            })
        ]).then(() => {
            console.log('Service Worker installed successfully');
            return self.skipWaiting();
        }).catch(error => {
            console.error('Service Worker installation failed:', error);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && 
                        cacheName !== STATIC_CACHE && 
                        cacheName !== DYNAMIC_CACHE) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker activated');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip external requests (except CDN resources)
    if (url.origin !== location.origin && !isCDNResource(url)) {
        return;
    }
    
    event.respondWith(
        handleRequest(request)
    );
});

async function handleRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Strategy 1: Static resources - Cache First
        if (isStaticResource(url)) {
            return await cacheFirst(request, STATIC_CACHE);
        }
        
        // Strategy 2: API requests - Network First
        if (isAPIRequest(url)) {
            return await networkFirst(request, DYNAMIC_CACHE);
        }
        
        // Strategy 3: Pages - Stale While Revalidate
        if (isPageRequest(url)) {
            return await staleWhileRevalidate(request, CACHE_NAME);
        }
        
        // Strategy 4: Images - Cache First with fallback
        if (isImageRequest(url)) {
            return await cacheFirstWithFallback(request, DYNAMIC_CACHE);
        }
        
        // Default: Network First
        return await networkFirst(request, DYNAMIC_CACHE);
        
    } catch (error) {
        console.error('Request handling failed:', error);
        return await getOfflineFallback(request);
    }
}

// Caching strategies
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        throw error;
    }
}

async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    // Always try to update cache in background
    const networkResponsePromise = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => {
        // Ignore network errors for background updates
    });
    
    // Return cached version immediately if available
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Wait for network if no cache
    return await networkResponsePromise;
}

async function cacheFirstWithFallback(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        // Return placeholder image for failed image requests
        if (isImageRequest(new URL(request.url))) {
            return await getPlaceholderImage();
        }
        throw error;
    }
}

// Helper functions
function isStaticResource(url) {
    return url.pathname.startsWith('/static/') || 
           isCDNResource(url) ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.woff') ||
           url.pathname.endsWith('.woff2');
}

function isAPIRequest(url) {
    return url.pathname.startsWith('/api/') ||
           url.pathname.startsWith('/insurance/api/');
}

function isPageRequest(url) {
    return url.pathname.startsWith('/insurance/') &&
           !url.pathname.startsWith('/insurance/api/') &&
           !isStaticResource(url) &&
           !isImageRequest(url);
}

function isImageRequest(url) {
    return /\.(jpg|jpeg|png|gif|webp|svg|ico)$/i.test(url.pathname);
}

function isCDNResource(url) {
    const cdnDomains = [
        'cdn.tailwindcss.com',
        'cdnjs.cloudflare.com',
        'fonts.googleapis.com',
        'fonts.gstatic.com'
    ];
    return cdnDomains.some(domain => url.hostname.includes(domain));
}

async function getOfflineFallback(request) {
    const url = new URL(request.url);
    
    if (isPageRequest(url)) {
        return await getOfflinePage();
    }
    
    if (isImageRequest(url)) {
        return await getPlaceholderImage();
    }
    
    return new Response('Offline', {
        status: 503,
        statusText: 'Service Unavailable'
    });
}

async function getOfflinePage() {
    const offlineHTML = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Offline - Insurance Dashboard</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: #f9fafb;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }
                .offline-container {
                    text-align: center;
                    padding: 2rem;
                    background: white;
                    border-radius: 0.75rem;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                }
                .offline-icon {
                    font-size: 4rem;
                    color: #6b7280;
                    margin-bottom: 1rem;
                }
                .offline-title {
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 0.5rem;
                }
                .offline-message {
                    color: #6b7280;
                    margin-bottom: 1.5rem;
                }
                .retry-button {
                    background: #1e40af;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-weight: 500;
                }
                .retry-button:hover {
                    background: #1d4ed8;
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <div class="offline-icon">📡</div>
                <h1 class="offline-title">You're Offline</h1>
                <p class="offline-message">
                    Please check your internet connection and try again.
                </p>
                <button class="retry-button" onclick="window.location.reload()">
                    Try Again
                </button>
            </div>
        </body>
        </html>
    `;
    
    return new Response(offlineHTML, {
        headers: { 'Content-Type': 'text/html' }
    });
}

async function getPlaceholderImage() {
    // Return a simple SVG placeholder
    const svg = `
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f3f4f6"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" 
                  font-family="Arial, sans-serif" font-size="18" fill="#9ca3af">
                Image Unavailable
            </text>
        </svg>
    `;
    
    return new Response(svg, {
        headers: { 'Content-Type': 'image/svg+xml' }
    });
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Handle offline actions when connection is restored
    console.log('Background sync triggered');
    
    // Process any queued API requests
    const queuedRequests = await getQueuedRequests();
    
    for (const request of queuedRequests) {
        try {
            await fetch(request.url, request.options);
            await removeQueuedRequest(request.id);
        } catch (error) {
            console.error('Background sync failed for request:', error);
        }
    }
}

async function getQueuedRequests() {
    // Implementation would retrieve queued requests from IndexedDB
    return [];
}

async function removeQueuedRequest(id) {
    // Implementation would remove request from IndexedDB
}

// Push notifications
self.addEventListener('push', event => {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body,
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            tag: data.tag || 'default',
            data: data.data || {},
            actions: data.actions || []
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    const data = event.notification.data;
    
    if (data && data.url) {
        event.waitUntil(
            clients.openWindow(data.url)
        );
    }
});

// Message handling from main thread
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

console.log('Service Worker loaded');