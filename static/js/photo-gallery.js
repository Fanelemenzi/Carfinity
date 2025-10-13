/**
 * Enhanced Photo Gallery System for Insurance Assessment
 * Implements full-screen modal with navigation, zoom, and metadata display
 */

class PhotoGallery {
    constructor() {
        this.currentPhotoSet = [];
        this.currentPhotoIndex = 0;
        this.zoomLevel = 1;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.imageOffset = { x: 0, y: 0 };
        this.isFullscreen = false;
        this.isComparisonMode = false;
        this.comparisonType = 'sideBySide'; // 'sideBySide' or 'overlay'
        this.sliderPosition = 50; // For overlay comparison
        
        this.initializeModal();
        this.bindEvents();
    }
    
    initializeModal() {
        // Create enhanced modal HTML if it doesn't exist
        if (!document.getElementById('enhancedPhotoModal')) {
            const modalHTML = `
                <div id="enhancedPhotoModal" class="fixed inset-0 bg-black bg-opacity-90 z-50 hidden">
                    <!-- Modal Header -->
                    <div id="modalHeader" class="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/70 to-transparent z-10 p-4 transition-opacity duration-300">
                        <div class="flex items-center justify-between text-white">
                            <div class="flex items-center space-x-4">
                                <h3 id="modalTitle" class="text-lg font-semibold"></h3>
                                <span id="photoCounter" class="text-sm opacity-75"></span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button id="fullscreenBtn" class="p-2 hover:bg-white/20 rounded-lg transition-colors" title="Toggle Fullscreen">
                                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                    </svg>
                                </button>
                                <button id="closeModalBtn" class="p-2 hover:bg-white/20 rounded-lg transition-colors" title="Close">
                                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Main Image Container -->
                    <div id="imageContainer" class="absolute inset-0 flex items-center justify-center overflow-hidden">
                        <img id="modalImage" src="" alt="" class="max-w-full max-h-full object-contain cursor-grab transition-transform duration-200" draggable="false">
                        
                        <!-- Loading Spinner -->
                        <div id="imageLoader" class="absolute inset-0 flex items-center justify-center">
                            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                        </div>
                    </div>
                    
                    <!-- Comparison Mode Container -->
                    <div id="comparisonContainer" class="absolute inset-0 hidden">
                        <!-- Side-by-Side Comparison -->
                        <div id="sideBySideComparison" class="flex h-full">
                            <div class="flex-1 flex items-center justify-center bg-black/20 border-r border-white/20">
                                <div class="text-center">
                                    <img id="beforeImage" src="" alt="Before" class="max-w-full max-h-full object-contain">
                                    <div class="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-lg text-sm font-medium">
                                        BEFORE
                                    </div>
                                </div>
                            </div>
                            <div class="flex-1 flex items-center justify-center bg-black/20">
                                <div class="text-center">
                                    <img id="afterImage" src="" alt="After" class="max-w-full max-h-full object-contain">
                                    <div class="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-lg text-sm font-medium">
                                        AFTER
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Overlay Comparison with Slider -->
                        <div id="overlayComparison" class="relative w-full h-full hidden">
                            <div class="absolute inset-0 flex items-center justify-center">
                                <div id="overlayContainer" class="relative max-w-full max-h-full">
                                    <img id="overlayBeforeImage" src="" alt="Before" class="w-full h-full object-contain">
                                    <div id="overlayAfterContainer" class="absolute inset-0 overflow-hidden" style="clip-path: inset(0 50% 0 0);">
                                        <img id="overlayAfterImage" src="" alt="After" class="w-full h-full object-contain">
                                    </div>
                                    
                                    <!-- Comparison Slider -->
                                    <div id="comparisonSlider" class="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize" style="left: 50%; transform: translateX(-50%);">
                                        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full border-2 border-gray-300 flex items-center justify-center">
                                            <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                                            </svg>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Comparison Controls -->
                        <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 rounded-lg p-2">
                            <div class="flex items-center space-x-2">
                                <button id="sideBySideBtn" class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors">
                                    Side by Side
                                </button>
                                <button id="overlayBtn" class="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors">
                                    Overlay
                                </button>
                                <button id="exitComparisonBtn" class="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors">
                                    Exit Comparison
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Navigation Arrows -->
                    <button id="prevPhotoBtn" class="absolute left-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full transition-all duration-200 opacity-0">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                        </svg>
                    </button>
                    
                    <button id="nextPhotoBtn" class="absolute right-4 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full transition-all duration-200 opacity-0">
                        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                    
                    <!-- Bottom Controls -->
                    <div id="modalFooter" class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent z-10 p-4 transition-opacity duration-300">
                        <div class="flex items-center justify-between text-white">
                            <!-- Photo Metadata -->
                            <div id="photoMetadata" class="flex-1 mr-4">
                                <p id="photoDescription" class="text-sm mb-1"></p>
                                <div class="flex items-center space-x-4 text-xs opacity-75">
                                    <span id="photoDate"></span>
                                    <span id="photoAssessor"></span>
                                    <span id="photoSection"></span>
                                </div>
                            </div>
                            
                            <!-- Zoom and Action Controls -->
                            <div class="flex items-center space-x-2">
                                <!-- Comparison Mode Toggle -->
                                <button id="comparisonModeBtn" class="px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors text-sm hidden">
                                    Compare
                                </button>
                                
                                <div class="flex items-center space-x-1 bg-black/50 rounded-lg p-1">
                                    <button id="zoomOutBtn" class="p-2 hover:bg-white/20 rounded transition-colors" title="Zoom Out">
                                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                                        </svg>
                                    </button>
                                    <span id="zoomLevel" class="px-2 text-xs">100%</span>
                                    <button id="zoomInBtn" class="p-2 hover:bg-white/20 rounded transition-colors" title="Zoom In">
                                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                                        </svg>
                                    </button>
                                    <button id="resetZoomBtn" class="p-2 hover:bg-white/20 rounded transition-colors" title="Reset Zoom">
                                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                </div>
                                
                                <button id="downloadBtn" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm">
                                    Download
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Photo Organization Panel -->
                    <div id="photoOrganizationPanel" class="absolute top-16 right-4 bg-black/70 rounded-lg p-4 text-white max-w-xs hidden">
                        <h4 class="text-sm font-semibold mb-3">Photo Organization</h4>
                        
                        <!-- Category Filter -->
                        <div class="mb-3">
                            <label class="text-xs text-gray-300 mb-1 block">Filter by Category:</label>
                            <select id="categoryFilter" class="w-full bg-black/50 border border-gray-600 rounded px-2 py-1 text-xs">
                                <option value="all">All Categories</option>
                                <option value="overall">Overall Vehicle</option>
                                <option value="damage">Damage Detail</option>
                                <option value="interior">Interior</option>
                                <option value="engine">Engine Bay</option>
                                <option value="undercarriage">Undercarriage</option>
                                <option value="documents">Documentation</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        
                        <!-- Section Filter -->
                        <div class="mb-3">
                            <label class="text-xs text-gray-300 mb-1 block">Filter by Section:</label>
                            <select id="sectionFilter" class="w-full bg-black/50 border border-gray-600 rounded px-2 py-1 text-xs">
                                <option value="all">All Sections</option>
                            </select>
                        </div>
                        
                        <!-- Photo Type Filter -->
                        <div class="mb-3">
                            <label class="text-xs text-gray-300 mb-1 block">Photo Type:</label>
                            <div class="flex flex-wrap gap-1">
                                <button id="filterPrimary" class="px-2 py-1 bg-blue-600 rounded text-xs hover:bg-blue-700 transition-colors">Primary</button>
                                <button id="filterDamage" class="px-2 py-1 bg-red-600 rounded text-xs hover:bg-red-700 transition-colors">Damage</button>
                                <button id="filterAll" class="px-2 py-1 bg-gray-600 rounded text-xs hover:bg-gray-700 transition-colors active">All</button>
                            </div>
                        </div>
                        
                        <!-- Sort Options -->
                        <div class="mb-3">
                            <label class="text-xs text-gray-300 mb-1 block">Sort by:</label>
                            <select id="sortOptions" class="w-full bg-black/50 border border-gray-600 rounded px-2 py-1 text-xs">
                                <option value="date">Date Taken</option>
                                <option value="section">Section</option>
                                <option value="category">Category</option>
                                <option value="primary">Primary First</option>
                            </select>
                        </div>
                        
                        <div class="text-xs text-gray-400 mt-2">
                            <span id="filteredCount">0</span> of <span id="totalCount">0</span> photos
                        </div>
                    </div>
                    
                    <!-- Photo Thumbnails Strip (for navigation) -->
                    <div id="thumbnailStrip" class="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-black/50 rounded-lg p-2 max-w-2xl overflow-x-auto hidden">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs text-gray-300">Quick Navigation</span>
                            <button id="toggleOrganization" class="text-xs text-blue-400 hover:text-blue-300">
                                Organize
                            </button>
                        </div>
                        <div id="thumbnailContainer" class="flex space-x-2"></div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }
    
    bindEvents() {
        const modal = document.getElementById('enhancedPhotoModal');
        const modalImage = document.getElementById('modalImage');
        const imageContainer = document.getElementById('imageContainer');
        
        // Close modal events
        document.getElementById('closeModalBtn').addEventListener('click', () => this.closeModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target === imageContainer) {
                this.closeModal();
            }
        });
        
        // Navigation events
        document.getElementById('prevPhotoBtn').addEventListener('click', () => this.navigatePhoto(-1));
        document.getElementById('nextPhotoBtn').addEventListener('click', () => this.navigatePhoto(1));
        
        // Zoom events
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoomOut());
        document.getElementById('resetZoomBtn').addEventListener('click', () => this.resetZoom());
        
        // Fullscreen event
        document.getElementById('fullscreenBtn').addEventListener('click', () => this.toggleFullscreen());
        
        // Download event
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadCurrentPhoto());
        
        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Mouse events for zoom and pan
        modalImage.addEventListener('wheel', (e) => this.handleWheel(e));
        modalImage.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.handleDrag(e));
        document.addEventListener('mouseup', () => this.endDrag());
        
        // Touch events for mobile
        modalImage.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        modalImage.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        modalImage.addEventListener('touchend', () => this.handleTouchEnd());
        
        // Image load events
        modalImage.addEventListener('load', () => this.onImageLoad());
        modalImage.addEventListener('error', () => this.onImageError());
        
        // Photo organization events
        document.getElementById('toggleOrganization').addEventListener('click', () => this.toggleOrganizationPanel());
        document.getElementById('categoryFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('sectionFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('sortOptions').addEventListener('change', () => this.applySorting());
        
        // Photo type filter buttons
        document.getElementById('filterPrimary').addEventListener('click', () => this.filterByType('primary'));
        document.getElementById('filterDamage').addEventListener('click', () => this.filterByType('damage'));
        document.getElementById('filterAll').addEventListener('click', () => this.filterByType('all'));
        
        // Comparison mode events
        document.getElementById('comparisonModeBtn').addEventListener('click', () => this.enterComparisonMode());
        document.getElementById('sideBySideBtn').addEventListener('click', () => this.setComparisonType('sideBySide'));
        document.getElementById('overlayBtn').addEventListener('click', () => this.setComparisonType('overlay'));
        document.getElementById('exitComparisonBtn').addEventListener('click', () => this.exitComparisonMode());
        
        // Comparison slider events
        document.getElementById('comparisonSlider').addEventListener('mousedown', (e) => this.startSliderDrag(e));
        document.addEventListener('mousemove', (e) => this.handleSliderDrag(e));
        document.addEventListener('mouseup', () => this.endSliderDrag());
        
        // Auto-hide controls
        let hideControlsTimeout;
        modal.addEventListener('mousemove', () => {
            this.showControls();
            clearTimeout(hideControlsTimeout);
            hideControlsTimeout = setTimeout(() => this.hideControls(), 3000);
        });
    }
    
    openPhotoModal(photos, startIndex = 0, title = '') {
        this.currentPhotoSet = Array.isArray(photos) ? photos : [photos];
        this.currentPhotoIndex = Math.max(0, Math.min(startIndex, this.currentPhotoSet.length - 1));
        this.filteredPhotoSet = null; // Reset filters
        
        const modal = document.getElementById('enhancedPhotoModal');
        const modalTitle = document.getElementById('modalTitle');
        
        modalTitle.textContent = title || 'Assessment Photos';
        
        this.resetZoom();
        this.updatePhoto();
        this.updateNavigation();
        this.updateThumbnails();
        this.initializeOrganizationPanel();
        
        // Hide organization panel initially
        document.getElementById('photoOrganizationPanel').classList.add('hidden');
        
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Show controls initially
        this.showControls();
        setTimeout(() => this.hideControls(), 3000);
    }
    
    closeModal() {
        const modal = document.getElementById('enhancedPhotoModal');
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        
        // Reset state
        this.currentPhotoSet = [];
        this.currentPhotoIndex = 0;
        this.resetZoom();
        
        // Exit comparison mode if active
        if (this.isComparisonMode) {
            this.exitComparisonMode();
        }
        
        if (this.isFullscreen) {
            this.exitFullscreen();
        }
    }
    
    updatePhoto() {
        if (this.currentPhotoSet.length === 0) return;
        
        const photo = this.currentPhotoSet[this.currentPhotoIndex];
        const modalImage = document.getElementById('modalImage');
        const imageLoader = document.getElementById('imageLoader');
        
        // Show loader
        imageLoader.style.display = 'flex';
        modalImage.style.opacity = '0';
        
        // Update image
        modalImage.src = photo.url || photo.image_url || photo.src;
        
        // Update metadata
        this.updateMetadata(photo);
        this.updateCounter();
        this.updateComparisonButton();
    }
    
    updateMetadata(photo) {
        const photoDescription = document.getElementById('photoDescription');
        const photoDate = document.getElementById('photoDate');
        const photoAssessor = document.getElementById('photoAssessor');
        const photoSection = document.getElementById('photoSection');
        
        photoDescription.textContent = photo.description || 'Assessment photo';
        photoDate.textContent = photo.taken_at ? new Date(photo.taken_at).toLocaleDateString() : '';
        photoAssessor.textContent = photo.assessor || '';
        photoSection.textContent = photo.section_reference || photo.category || '';
    }
    
    updateCounter() {
        const counter = document.getElementById('photoCounter');
        counter.textContent = `${this.currentPhotoIndex + 1} of ${this.currentPhotoSet.length}`;
    }
    
    updateNavigation() {
        const prevBtn = document.getElementById('prevPhotoBtn');
        const nextBtn = document.getElementById('nextPhotoBtn');
        
        if (this.currentPhotoSet.length > 1) {
            prevBtn.style.opacity = '1';
            nextBtn.style.opacity = '1';
            prevBtn.style.pointerEvents = 'auto';
            nextBtn.style.pointerEvents = 'auto';
        } else {
            prevBtn.style.opacity = '0';
            nextBtn.style.opacity = '0';
            prevBtn.style.pointerEvents = 'none';
            nextBtn.style.pointerEvents = 'none';
        }
    }
    
    updateThumbnails() {
        const thumbnailStrip = document.getElementById('thumbnailStrip');
        const thumbnailContainer = document.getElementById('thumbnailContainer');
        
        if (this.currentPhotoSet.length <= 1) {
            thumbnailStrip.classList.add('hidden');
            return;
        }
        
        thumbnailContainer.innerHTML = '';
        
        this.currentPhotoSet.forEach((photo, index) => {
            const thumbnail = document.createElement('div');
            thumbnail.className = `w-12 h-12 rounded cursor-pointer border-2 transition-all relative ${
                index === this.currentPhotoIndex ? 'border-blue-400' : 'border-transparent hover:border-white/50'
            }`;
            
            const img = document.createElement('img');
            img.src = photo.thumbnail_url || photo.url || photo.image_url || photo.src;
            img.className = 'w-full h-full object-cover rounded';
            img.addEventListener('click', () => this.goToPhoto(index));
            
            // Add primary photo indicator
            if (photo.is_primary) {
                const primaryIndicator = document.createElement('div');
                primaryIndicator.className = 'absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border border-white';
                thumbnail.appendChild(primaryIndicator);
            }
            
            // Add damage point indicator if available
            if (photo.damage_point_id) {
                const damageIndicator = document.createElement('div');
                damageIndicator.className = 'absolute -bottom-1 -left-1 w-3 h-3 bg-red-500 rounded-full border border-white';
                thumbnail.appendChild(damageIndicator);
            }
            
            thumbnail.appendChild(img);
            thumbnailContainer.appendChild(thumbnail);
        });
        
        thumbnailStrip.classList.remove('hidden');
    }
    
    navigatePhoto(direction) {
        if (this.currentPhotoSet.length <= 1) return;
        
        this.currentPhotoIndex += direction;
        
        if (this.currentPhotoIndex < 0) {
            this.currentPhotoIndex = this.currentPhotoSet.length - 1;
        } else if (this.currentPhotoIndex >= this.currentPhotoSet.length) {
            this.currentPhotoIndex = 0;
        }
        
        this.resetZoom();
        this.updatePhoto();
        this.updateThumbnails();
    }
    
    goToPhoto(index) {
        if (index >= 0 && index < this.currentPhotoSet.length) {
            this.currentPhotoIndex = index;
            this.resetZoom();
            this.updatePhoto();
            this.updateThumbnails();
        }
    }
    
    // Zoom functionality
    zoomIn() {
        this.zoomLevel = Math.min(this.zoomLevel * 1.25, 5);
        this.applyZoom();
    }
    
    zoomOut() {
        this.zoomLevel = Math.max(this.zoomLevel / 1.25, 0.25);
        this.applyZoom();
    }
    
    resetZoom() {
        this.zoomLevel = 1;
        this.imageOffset = { x: 0, y: 0 };
        this.applyZoom();
    }
    
    applyZoom() {
        const modalImage = document.getElementById('modalImage');
        const zoomLevelDisplay = document.getElementById('zoomLevel');
        
        modalImage.style.transform = `scale(${this.zoomLevel}) translate(${this.imageOffset.x}px, ${this.imageOffset.y}px)`;
        modalImage.style.cursor = this.zoomLevel > 1 ? 'grab' : 'default';
        
        zoomLevelDisplay.textContent = `${Math.round(this.zoomLevel * 100)}%`;
    }
    
    // Event handlers
    handleKeyboard(e) {
        if (!document.getElementById('enhancedPhotoModal').classList.contains('hidden')) {
            switch (e.key) {
                case 'Escape':
                    this.closeModal();
                    break;
                case 'ArrowLeft':
                    this.navigatePhoto(-1);
                    break;
                case 'ArrowRight':
                    this.navigatePhoto(1);
                    break;
                case '+':
                case '=':
                    this.zoomIn();
                    break;
                case '-':
                    this.zoomOut();
                    break;
                case '0':
                    this.resetZoom();
                    break;
                case 'f':
                case 'F':
                    this.toggleFullscreen();
                    break;
            }
        }
    }
    
    handleWheel(e) {
        e.preventDefault();
        
        if (e.deltaY < 0) {
            this.zoomIn();
        } else {
            this.zoomOut();
        }
    }
    
    startDrag(e) {
        if (this.zoomLevel > 1) {
            this.isDragging = true;
            this.dragStart = { x: e.clientX, y: e.clientY };
            document.getElementById('modalImage').style.cursor = 'grabbing';
        }
    }
    
    handleDrag(e) {
        if (this.isDragging && this.zoomLevel > 1) {
            const deltaX = e.clientX - this.dragStart.x;
            const deltaY = e.clientY - this.dragStart.y;
            
            this.imageOffset.x += deltaX / this.zoomLevel;
            this.imageOffset.y += deltaY / this.zoomLevel;
            
            this.dragStart = { x: e.clientX, y: e.clientY };
            this.applyZoom();
        }
    }
    
    endDrag() {
        this.isDragging = false;
        if (this.zoomLevel > 1) {
            document.getElementById('modalImage').style.cursor = 'grab';
        }
    }
    
    // Touch events for mobile
    handleTouchStart(e) {
        if (e.touches.length === 1 && this.zoomLevel > 1) {
            this.isDragging = true;
            this.dragStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        }
    }
    
    handleTouchMove(e) {
        if (this.isDragging && e.touches.length === 1 && this.zoomLevel > 1) {
            e.preventDefault();
            const deltaX = e.touches[0].clientX - this.dragStart.x;
            const deltaY = e.touches[0].clientY - this.dragStart.y;
            
            this.imageOffset.x += deltaX / this.zoomLevel;
            this.imageOffset.y += deltaY / this.zoomLevel;
            
            this.dragStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            this.applyZoom();
        }
    }
    
    handleTouchEnd() {
        this.isDragging = false;
    }
    
    onImageLoad() {
        const imageLoader = document.getElementById('imageLoader');
        const modalImage = document.getElementById('modalImage');
        
        imageLoader.style.display = 'none';
        modalImage.style.opacity = '1';
    }
    
    onImageError() {
        const imageLoader = document.getElementById('imageLoader');
        const modalImage = document.getElementById('modalImage');
        
        imageLoader.style.display = 'none';
        modalImage.src = '/static/images/image-error.png'; // Fallback image
        modalImage.style.opacity = '1';
    }
    
    showControls() {
        const header = document.getElementById('modalHeader');
        const footer = document.getElementById('modalFooter');
        const thumbnails = document.getElementById('thumbnailStrip');
        
        header.style.opacity = '1';
        footer.style.opacity = '1';
        if (!thumbnails.classList.contains('hidden')) {
            thumbnails.style.opacity = '1';
        }
    }
    
    hideControls() {
        const header = document.getElementById('modalHeader');
        const footer = document.getElementById('modalFooter');
        const thumbnails = document.getElementById('thumbnailStrip');
        
        header.style.opacity = '0';
        footer.style.opacity = '0';
        thumbnails.style.opacity = '0';
    }
    
    toggleFullscreen() {
        if (!this.isFullscreen) {
            this.enterFullscreen();
        } else {
            this.exitFullscreen();
        }
    }
    
    enterFullscreen() {
        const modal = document.getElementById('enhancedPhotoModal');
        
        if (modal.requestFullscreen) {
            modal.requestFullscreen();
        } else if (modal.webkitRequestFullscreen) {
            modal.webkitRequestFullscreen();
        } else if (modal.msRequestFullscreen) {
            modal.msRequestFullscreen();
        }
        
        this.isFullscreen = true;
    }
    
    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        
        this.isFullscreen = false;
    }
    
    downloadCurrentPhoto() {
        if (this.currentPhotoSet.length === 0) return;
        
        const photo = this.currentPhotoSet[this.currentPhotoIndex];
        const link = document.createElement('a');
        link.href = photo.url || photo.image_url || photo.src;
        link.download = `assessment-photo-${this.currentPhotoIndex + 1}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Photo Organization Methods
    toggleOrganizationPanel() {
        const panel = document.getElementById('photoOrganizationPanel');
        panel.classList.toggle('hidden');
        
        if (!panel.classList.contains('hidden')) {
            this.initializeOrganizationPanel();
        }
    }
    
    initializeOrganizationPanel() {
        // Populate section filter options
        const sectionFilter = document.getElementById('sectionFilter');
        const sections = [...new Set(this.currentPhotoSet.map(photo => photo.section_reference).filter(Boolean))];
        
        sectionFilter.innerHTML = '<option value="all">All Sections</option>';
        sections.forEach(section => {
            const option = document.createElement('option');
            option.value = section;
            option.textContent = section;
            sectionFilter.appendChild(option);
        });
        
        // Update counts
        this.updateFilterCounts();
    }
    
    applyFilters() {
        const categoryFilter = document.getElementById('categoryFilter').value;
        const sectionFilter = document.getElementById('sectionFilter').value;
        
        this.filteredPhotoSet = this.currentPhotoSet.filter(photo => {
            const categoryMatch = categoryFilter === 'all' || photo.category === categoryFilter;
            const sectionMatch = sectionFilter === 'all' || photo.section_reference === sectionFilter;
            
            return categoryMatch && sectionMatch;
        });
        
        this.applySorting();
        this.updateFilterCounts();
        this.rebuildThumbnails();
        
        // Adjust current index if needed
        if (this.currentPhotoIndex >= this.filteredPhotoSet.length) {
            this.currentPhotoIndex = Math.max(0, this.filteredPhotoSet.length - 1);
            this.updatePhoto();
        }
    }
    
    filterByType(type) {
        // Update button states
        document.querySelectorAll('#photoOrganizationPanel button').forEach(btn => {
            btn.classList.remove('active', 'bg-blue-700', 'bg-red-700', 'bg-gray-700');
        });
        
        let activeButton;
        switch (type) {
            case 'primary':
                this.filteredPhotoSet = this.currentPhotoSet.filter(photo => photo.is_primary);
                activeButton = document.getElementById('filterPrimary');
                activeButton.classList.add('active', 'bg-blue-700');
                break;
            case 'damage':
                this.filteredPhotoSet = this.currentPhotoSet.filter(photo => photo.damage_point_id);
                activeButton = document.getElementById('filterDamage');
                activeButton.classList.add('active', 'bg-red-700');
                break;
            default:
                this.filteredPhotoSet = [...this.currentPhotoSet];
                activeButton = document.getElementById('filterAll');
                activeButton.classList.add('active', 'bg-gray-700');
        }
        
        this.applySorting();
        this.updateFilterCounts();
        this.rebuildThumbnails();
        
        // Reset to first photo of filtered set
        this.currentPhotoIndex = 0;
        this.updatePhoto();
    }
    
    applySorting() {
        const sortOption = document.getElementById('sortOptions').value;
        
        if (!this.filteredPhotoSet) {
            this.filteredPhotoSet = [...this.currentPhotoSet];
        }
        
        switch (sortOption) {
            case 'date':
                this.filteredPhotoSet.sort((a, b) => new Date(b.taken_at || 0) - new Date(a.taken_at || 0));
                break;
            case 'section':
                this.filteredPhotoSet.sort((a, b) => (a.section_reference || '').localeCompare(b.section_reference || ''));
                break;
            case 'category':
                this.filteredPhotoSet.sort((a, b) => (a.category || '').localeCompare(b.category || ''));
                break;
            case 'primary':
                this.filteredPhotoSet.sort((a, b) => (b.is_primary ? 1 : 0) - (a.is_primary ? 1 : 0));
                break;
        }
    }
    
    updateFilterCounts() {
        const totalCount = document.getElementById('totalCount');
        const filteredCount = document.getElementById('filteredCount');
        
        totalCount.textContent = this.currentPhotoSet.length;
        filteredCount.textContent = this.filteredPhotoSet ? this.filteredPhotoSet.length : this.currentPhotoSet.length;
    }
    
    rebuildThumbnails() {
        const thumbnailContainer = document.getElementById('thumbnailContainer');
        const photoSet = this.filteredPhotoSet || this.currentPhotoSet;
        
        thumbnailContainer.innerHTML = '';
        
        photoSet.forEach((photo, index) => {
            const thumbnail = document.createElement('div');
            thumbnail.className = `w-12 h-12 rounded cursor-pointer border-2 transition-all relative ${
                index === this.currentPhotoIndex ? 'border-blue-400' : 'border-transparent hover:border-white/50'
            }`;
            
            const img = document.createElement('img');
            img.src = photo.thumbnail_url || photo.url || photo.image_url || photo.src;
            img.className = 'w-full h-full object-cover rounded';
            img.addEventListener('click', () => this.goToFilteredPhoto(index));
            
            // Add indicators
            if (photo.is_primary) {
                const primaryIndicator = document.createElement('div');
                primaryIndicator.className = 'absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border border-white';
                primaryIndicator.title = 'Primary Photo';
                thumbnail.appendChild(primaryIndicator);
            }
            
            if (photo.damage_point_id) {
                const damageIndicator = document.createElement('div');
                damageIndicator.className = 'absolute -bottom-1 -left-1 w-3 h-3 bg-red-500 rounded-full border border-white';
                damageIndicator.title = 'Damage Point';
                thumbnail.appendChild(damageIndicator);
            }
            
            thumbnail.appendChild(img);
            thumbnailContainer.appendChild(thumbnail);
        });
    }
    
    goToFilteredPhoto(filteredIndex) {
        if (this.filteredPhotoSet && filteredIndex >= 0 && filteredIndex < this.filteredPhotoSet.length) {
            // Find the original index of this photo
            const photo = this.filteredPhotoSet[filteredIndex];
            const originalIndex = this.currentPhotoSet.findIndex(p => p === photo);
            
            this.currentPhotoIndex = originalIndex;
            this.updatePhoto();
            this.rebuildThumbnails();
        }
    }
    
    // Before/After Comparison Methods
    detectBeforeAfterPhotos() {
        const currentPhoto = this.currentPhotoSet[this.currentPhotoIndex];
        const damagePointId = currentPhoto.damage_point_id;
        
        if (!damagePointId) return null;
        
        // Find photos with the same damage point
        const relatedPhotos = this.currentPhotoSet.filter(photo => 
            photo.damage_point_id === damagePointId && photo !== currentPhoto
        );
        
        if (relatedPhotos.length === 0) return null;
        
        // Try to identify before/after based on description or timestamp
        const beforePhoto = this.identifyBeforePhoto(currentPhoto, relatedPhotos);
        const afterPhoto = this.identifyAfterPhoto(currentPhoto, relatedPhotos);
        
        if (beforePhoto && afterPhoto) {
            return { before: beforePhoto, after: afterPhoto };
        }
        
        // If we can't identify before/after, use current and first related photo
        return { before: currentPhoto, after: relatedPhotos[0] };
    }
    
    identifyBeforePhoto(currentPhoto, relatedPhotos) {
        // Look for photos with temporal sequence "before"
        const beforeBySequence = relatedPhotos.find(photo => 
            photo.temporal_sequence && photo.temporal_sequence.toLowerCase() === 'before'
        );
        if (beforeBySequence) return beforeBySequence;
        
        // Look for photos with "before" in description
        const beforeByDescription = relatedPhotos.find(photo => 
            photo.description && photo.description.toLowerCase().includes('before')
        );
        if (beforeByDescription) return beforeByDescription;
        
        // Look for earlier timestamp
        const currentTime = new Date(currentPhoto.taken_at || 0);
        const earlierPhotos = relatedPhotos.filter(photo => 
            new Date(photo.taken_at || 0) < currentTime
        );
        
        if (earlierPhotos.length > 0) {
            return earlierPhotos.sort((a, b) => new Date(a.taken_at || 0) - new Date(b.taken_at || 0))[0];
        }
        
        return currentPhoto;
    }
    
    identifyAfterPhoto(currentPhoto, relatedPhotos) {
        // Look for photos with temporal sequence "after"
        const afterBySequence = relatedPhotos.find(photo => 
            photo.temporal_sequence && photo.temporal_sequence.toLowerCase() === 'after'
        );
        if (afterBySequence) return afterBySequence;
        
        // Look for photos with "after" in description
        const afterByDescription = relatedPhotos.find(photo => 
            photo.description && photo.description.toLowerCase().includes('after')
        );
        if (afterByDescription) return afterByDescription;
        
        // Look for later timestamp
        const currentTime = new Date(currentPhoto.taken_at || 0);
        const laterPhotos = relatedPhotos.filter(photo => 
            new Date(photo.taken_at || 0) > currentTime
        );
        
        if (laterPhotos.length > 0) {
            return laterPhotos.sort((a, b) => new Date(b.taken_at || 0) - new Date(a.taken_at || 0))[0];
        }
        
        return relatedPhotos[0];
    }
    
    enterComparisonMode() {
        const comparisonPhotos = this.detectBeforeAfterPhotos();
        
        if (!comparisonPhotos) {
            alert('No related photos found for comparison. Photos must have the same damage point ID.');
            return;
        }
        
        this.isComparisonMode = true;
        
        // Hide single image container
        document.getElementById('imageContainer').classList.add('hidden');
        
        // Show comparison container
        const comparisonContainer = document.getElementById('comparisonContainer');
        comparisonContainer.classList.remove('hidden');
        
        // Load comparison images
        this.loadComparisonImages(comparisonPhotos.before, comparisonPhotos.after);
        
        // Set initial comparison type
        this.setComparisonType('sideBySide');
        
        // Hide comparison button
        document.getElementById('comparisonModeBtn').classList.add('hidden');
    }
    
    exitComparisonMode() {
        this.isComparisonMode = false;
        
        // Show single image container
        document.getElementById('imageContainer').classList.remove('hidden');
        
        // Hide comparison container
        document.getElementById('comparisonContainer').classList.add('hidden');
        
        // Show comparison button if applicable
        this.updateComparisonButton();
    }
    
    loadComparisonImages(beforePhoto, afterPhoto) {
        // Load side-by-side images
        document.getElementById('beforeImage').src = beforePhoto.url || beforePhoto.image_url || beforePhoto.src;
        document.getElementById('afterImage').src = afterPhoto.url || afterPhoto.image_url || afterPhoto.src;
        
        // Load overlay images
        document.getElementById('overlayBeforeImage').src = beforePhoto.url || beforePhoto.image_url || beforePhoto.src;
        document.getElementById('overlayAfterImage').src = afterPhoto.url || afterPhoto.image_url || afterPhoto.src;
        
        // Update metadata for comparison
        const photoDescription = document.getElementById('photoDescription');
        photoDescription.textContent = `Comparing: ${beforePhoto.description || 'Before'} vs ${afterPhoto.description || 'After'}`;
    }
    
    setComparisonType(type) {
        this.comparisonType = type;
        
        const sideBySideContainer = document.getElementById('sideBySideComparison');
        const overlayContainer = document.getElementById('overlayComparison');
        const sideBySideBtn = document.getElementById('sideBySideBtn');
        const overlayBtn = document.getElementById('overlayBtn');
        
        if (type === 'sideBySide') {
            sideBySideContainer.classList.remove('hidden');
            overlayContainer.classList.add('hidden');
            sideBySideBtn.classList.add('bg-blue-600');
            sideBySideBtn.classList.remove('bg-gray-600');
            overlayBtn.classList.add('bg-gray-600');
            overlayBtn.classList.remove('bg-blue-600');
        } else {
            sideBySideContainer.classList.add('hidden');
            overlayContainer.classList.remove('hidden');
            overlayBtn.classList.add('bg-blue-600');
            overlayBtn.classList.remove('bg-gray-600');
            sideBySideBtn.classList.add('bg-gray-600');
            sideBySideBtn.classList.remove('bg-blue-600');
        }
    }
    
    updateComparisonButton() {
        const comparisonBtn = document.getElementById('comparisonModeBtn');
        const comparisonPhotos = this.detectBeforeAfterPhotos();
        
        if (comparisonPhotos && !this.isComparisonMode) {
            comparisonBtn.classList.remove('hidden');
        } else {
            comparisonBtn.classList.add('hidden');
        }
    }
    
    // Slider functionality for overlay comparison
    startSliderDrag(e) {
        this.isSliderDragging = true;
        e.preventDefault();
    }
    
    handleSliderDrag(e) {
        if (!this.isSliderDragging || this.comparisonType !== 'overlay') return;
        
        const overlayContainer = document.getElementById('overlayContainer');
        const rect = overlayContainer.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
        
        this.sliderPosition = percentage;
        this.updateSliderPosition();
    }
    
    endSliderDrag() {
        this.isSliderDragging = false;
    }
    
    updateSliderPosition() {
        const slider = document.getElementById('comparisonSlider');
        const afterContainer = document.getElementById('overlayAfterContainer');
        
        slider.style.left = `${this.sliderPosition}%`;
        afterContainer.style.clipPath = `inset(0 ${100 - this.sliderPosition}% 0 0)`;
    }
}

// Initialize photo gallery when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.photoGallery = new PhotoGallery();
});

// Global functions for backward compatibility
function openPhotoModal(imageUrl, description, componentName) {
    const photo = {
        url: imageUrl,
        description: description,
        component: componentName,
        taken_at: new Date().toISOString()
    };
    
    window.photoGallery.openPhotoModal([photo], 0, componentName);
}

function closePhotoModal() {
    window.photoGallery.closeModal();
}