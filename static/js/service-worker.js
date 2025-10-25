/**
 * Service Worker for AutoCare Dashboard
 * Implements caching strategies for performance optimization
 */

const CACHE_NAME = 'autocare-dashboard-v1';
const STATIC_CACHE = 'autocare-static-v1';
const DYNAMIC_CACHE = 'autocare-dynamic-v1';

// Resources to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/css/dashboard-hover-effects.css',
    '/static/js/accessibility-enhancements.js',
    '/static/js/performance-optimization.js',
    '/static/js/dashboard-hover-interactions.js',
    '/static/js/dynamic-visual-feedback.js',
    '/static/js/mobile-interactions.js',
    '/static/images/carfinity logo.png',
    '/static/images/default-vehicle.png'
];

// Resources to cache on demand
const DYNAMIC_ASSETS = [
    '/api/',
    '/dashboard/',
    '/vehicles/',
    '/maintenance/',
    '/notifications/'
];

// Cache strategies
const CACHE_STRATEGIES = {
    CACHE_FIRST: 'cache-first',
    NETWORK_FIRST: 'network-first',
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
    NETWORK_ONLY: 'network-only',
    CACHE_ONLY: 'cache-only'
};

// Resource-specific cache strategies
const RESOURCE_STRATEGIES = {
    // Static assets - cache first
    '/static/': CACHE_STRATEGIES.CACHE_FIRST,
    '/images/': CACHE_STRATEGIES.CACHE_FIRST,
    
    // API endpoints - network first
    '/api/': CACHE_STRATEGIES.NETWORK_FIRST,
    
    // HTML pages - stale while revalidate
    '/dashboard/': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,
    '/vehicles/': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,
    
    // Real-time data - network only
    '/notifications/live/': CACHE_STRATEGIES.NETWORK_ONLY
};

// Cache expiration times (in milliseconds)
const CACHE_EXPIRATION = {
    STATIC: 7 * 24 * 60 * 60 * 1000, // 7 days
    DYNAMIC: 24 * 60 * 60 * 1000,    // 1 day
    API: 5 * 60 * 1000               // 5 minutes
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Failed to cache static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with appropriate caching strategy
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Determine cache strategy based on URL
    const strategy = getCacheStrategy(url.pathname);
    
    event.respondWith(
        handleRequest(request, strategy)
    );
});

// Determine cache strategy for a given path
function getCacheStrategy(pathname) {
    for (const [pattern, strategy] of Object.entries(RESOURCE_STRATEGIES)) {
        if (pathname.startsWith(pattern)) {
            return strategy;
        }
    }
    
    // Default strategy
    return CACHE_STRATEGIES.STALE_WHILE_REVALIDATE;
}

// Handle request with specified strategy
async function handleRequest(request, strategy) {
    switch (strategy) {
        case CACHE_STRATEGIES.CACHE_FIRST:
            return cacheFirst(request);
        case CACHE_STRATEGIES.NETWORK_FIRST:
            return networkFirst(request);
        case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
            return staleWhileRevalidate(request);
        case CACHE_STRATEGIES.NETWORK_ONLY:
            return networkOnly(request);
        case CACHE_STRATEGIES.CACHE_ONLY:
            return cacheOnly(request);
        default:
            return staleWhileRevalidate(request);
    }
}

// Cache First strategy
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse && !isExpired(cachedResponse)) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(getAppropriateCache(request.url));
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Cache first strategy failed:', error);
        
        // Fallback to cache even if expired
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return createErrorResponse('Resource not available offline');
    }
}

// Network First strategy
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(getAppropriateCache(request.url));
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Network first strategy failed:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return createErrorResponse('Network error and no cached version available');
    }
}

// Stale While Revalidate strategy
async function staleWhileRevalidate(request) {
    const cachedResponse = await caches.match(request);
    
    // Always try to fetch from network in background
    const networkResponsePromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                const cache = caches.open(getAppropriateCache(request.url));
                cache.then(c => c.put(request, networkResponse.clone()));
            }
            return networkResponse;
        })
        .catch((error) => {
            console.error('Background fetch failed:', error);
        });
    
    // Return cached response immediately if available
    if (cachedResponse && !isExpired(cachedResponse)) {
        return cachedResponse;
    }
    
    // If no cache or expired, wait for network
    try {
        return await networkResponsePromise;
    } catch (error) {
        // If network fails and we have cached response, return it
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return createErrorResponse('No cached version and network unavailable');
    }
}

// Network Only strategy
async function networkOnly(request) {
    try {
        return await fetch(request);
    } catch (error) {
        return createErrorResponse('Network error');
    }
}

// Cache Only strategy
async function cacheOnly(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    return createErrorResponse('Resource not in cache');
}

// Get appropriate cache for URL
function getAppropriateCache(url) {
    if (url.includes('/static/') || url.includes('/images/')) {
        return STATIC_CACHE;
    }
    return DYNAMIC_CACHE;
}

// Check if cached response is expired
function isExpired(response) {
    const cachedDate = response.headers.get('date');
    if (!cachedDate) return false;
    
    const cacheTime = new Date(cachedDate).getTime();
    const now = Date.now();
    
    // Determine expiration time based on URL
    let expirationTime = CACHE_EXPIRATION.DYNAMIC;
    
    if (response.url.includes('/static/') || response.url.includes('/images/')) {
        expirationTime = CACHE_EXPIRATION.STATIC;
    } else if (response.url.includes('/api/')) {
        expirationTime = CACHE_EXPIRATION.API;
    }
    
    return (now - cacheTime) > expirationTime;
}

// Create error response
function createErrorResponse(message) {
    return new Response(
        JSON.stringify({
            error: true,
            message: message,
            timestamp: new Date().toISOString()
        }),
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
                'Content-Type': 'application/json'
            }
        }
    );
}

// Background sync for failed requests
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(
            retryFailedRequests()
        );
    }
});

// Retry failed requests
async function retryFailedRequests() {
    // This would integrate with your failed request queue
    console.log('Retrying failed requests...');
    
    // Example implementation:
    // const failedRequests = await getFailedRequestsFromIndexedDB();
    // for (const request of failedRequests) {
    //     try {
    //         await fetch(request);
    //         await removeFromFailedRequests(request);
    //     } catch (error) {
    //         console.error('Retry failed:', error);
    //     }
    // }
}

// Push notification handling
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/static/images/carfinity logo.png',
        badge: '/static/images/notification-badge.png',
        vibrate: [200, 100, 200],
        data: data.data,
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const data = event.notification.data;
    
    event.waitUntil(
        clients.openWindow(data.url || '/')
    );
});

// Message handling from main thread
self.addEventListener('message', (event) => {
    const { type, payload } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
        case 'CACHE_RESOURCE':
            cacheResource(payload.url);
            break;
        case 'CLEAR_CACHE':
            clearCache(payload.cacheName);
            break;
        case 'GET_CACHE_STATUS':
            getCacheStatus().then(status => {
                event.ports[0].postMessage(status);
            });
            break;
    }
});

// Cache a specific resource
async function cacheResource(url) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        await cache.add(url);
        console.log('Resource cached:', url);
    } catch (error) {
        console.error('Failed to cache resource:', url, error);
    }
}

// Clear specific cache
async function clearCache(cacheName) {
    try {
        await caches.delete(cacheName);
        console.log('Cache cleared:', cacheName);
    } catch (error) {
        console.error('Failed to clear cache:', cacheName, error);
    }
}

// Get cache status
async function getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {};
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        status[cacheName] = {
            size: keys.length,
            resources: keys.map(request => request.url)
        };
    }
    
    return status;
}

// Periodic cache cleanup
setInterval(async () => {
    try {
        await cleanupExpiredCache();
    } catch (error) {
        console.error('Cache cleanup failed:', error);
    }
}, 60 * 60 * 1000); // Run every hour

// Clean up expired cache entries
async function cleanupExpiredCache() {
    const cacheNames = await caches.keys();
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            if (response && isExpired(response)) {
                await cache.delete(request);
                console.log('Removed expired cache entry:', request.url);
            }
        }
    }
}

console.log('Service Worker loaded');