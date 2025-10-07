var staticCacheName = 'carfinity-pwa-v2';

// List of URLs to cache during service worker installation
var urlsToCache = [
  '/',
  '/static/css/tailwind/tailwind.min.css',
  '/static/css/part-selector.css',
  '/static/js/serviceworker.js',
  '/static/images/icon.png',
  '/static/images/logo.svg',
  '/manifest.json'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(staticCacheName).then(function(cache) {
      // Cache resources individually to handle failures gracefully
      return Promise.all(
        urlsToCache.map(function(url) {
          return cache.add(url).catch(function(error) {
            console.warn('Failed to cache:', url, error);
            // Continue with other resources even if one fails
            return Promise.resolve();
          });
        })
      );
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== staticCacheName) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', function(event) {
  var requestUrl = new URL(event.request.url);
  
  // Only handle requests from the same origin
  if (requestUrl.origin === location.origin) {
    event.respondWith(
      caches.match(event.request).then(function(response) {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        
        return fetch(event.request, { credentials: 'include' }).then(function(response) {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          // Clone the response for caching
          var responseToCache = response.clone();
          
          caches.open(staticCacheName).then(function(cache) {
            cache.put(event.request, responseToCache);
          });
          
          return response;
        });
      })
    );
  }
});