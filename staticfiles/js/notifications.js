/**
 * Notification System JavaScript
 * Handles notification bell, dropdown, and real-time updates
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.isDropdownOpen = false;
        this.updateInterval = null;
        this.soundEnabled = true;
        
        this.init();
    }
    
    init() {
        this.createNotificationElements();
        this.bindEvents();
        this.loadNotifications();
        this.startPeriodicUpdates();
    }
    
    createNotificationElements() {
        // Find or create notification bell container
        let bellContainer = document.getElementById('notificationBell');
        
        if (!bellContainer) {
            // Create notification bell if it doesn't exist
            bellContainer = document.createElement('div');
            bellContainer.id = 'notificationBell';
            bellContainer.className = 'relative';
            
            // Find a suitable parent (usually in the header)
            const headerActions = document.querySelector('.flex.items-center.space-x-4, .flex.items-center.space-x-2');
            if (headerActions) {
                headerActions.insertBefore(bellContainer, headerActions.firstChild);
            }
        }
        
        // Create bell button HTML
        bellContainer.innerHTML = `
            <button class="notification-bell" 
                    id="notificationBellBtn" 
                    aria-label="Notifications" 
                    aria-expanded="false"
                    aria-haspopup="true">
                <i class="fas fa-bell bell-icon"></i>
                <span class="notification-badge" id="notificationBadge" style="display: none;">0</span>
            </button>
            
            <div class="notification-dropdown hidden" id="notificationDropdown" role="menu" aria-labelledby="notificationBellBtn">
                <div class="notification-header">
                    <h3 class="notification-title">Notifications</h3>
                    <div class="notification-actions">
                        <button class="notification-action-btn" id="markAllReadBtn" title="Mark all as read">
                            <i class="fas fa-check-double"></i>
                        </button>
                        <button class="notification-action-btn" id="notificationSettingsBtn" title="Settings">
                            <i class="fas fa-cog"></i>
                        </button>
                    </div>
                </div>
                
                <div class="notification-list" id="notificationList">
                    <div class="notification-loading">
                        <div class="notification-spinner"></div>
                        <p class="notification-loading-text">Loading notifications...</p>
                    </div>
                </div>
                
                <div class="notification-footer">
                    <a href="#" class="notification-footer-link" id="viewAllNotifications">View all notifications</a>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        const bellBtn = document.getElementById('notificationBellBtn');
        const dropdown = document.getElementById('notificationDropdown');
        const markAllReadBtn = document.getElementById('markAllReadBtn');
        const settingsBtn = document.getElementById('notificationSettingsBtn');
        
        // Bell button click
        if (bellBtn) {
            bellBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown();
            });
        }
        
        // Mark all as read
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
        
        // Settings button
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.openSettings();
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#notificationBell')) {
                this.closeDropdown();
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isDropdownOpen) {
                this.closeDropdown();
                bellBtn?.focus();
            }
        });
        
        // Handle dropdown keyboard navigation
        if (dropdown) {
            dropdown.addEventListener('keydown', (e) => {
                this.handleDropdownKeyboard(e);
            });
        }
    }
    
    toggleDropdown() {
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    openDropdown() {
        const dropdown = document.getElementById('notificationDropdown');
        const bellBtn = document.getElementById('notificationBellBtn');
        
        if (dropdown && bellBtn) {
            dropdown.classList.remove('hidden');
            dropdown.classList.add('show');
            bellBtn.setAttribute('aria-expanded', 'true');
            this.isDropdownOpen = true;
            
            // Focus first notification item
            setTimeout(() => {
                const firstItem = dropdown.querySelector('.notification-item');
                if (firstItem) {
                    firstItem.focus();
                }
            }, 100);
        }
    }
    
    closeDropdown() {
        const dropdown = document.getElementById('notificationDropdown');
        const bellBtn = document.getElementById('notificationBellBtn');
        
        if (dropdown && bellBtn) {
            dropdown.classList.remove('show');
            setTimeout(() => {
                dropdown.classList.add('hidden');
            }, 200);
            bellBtn.setAttribute('aria-expanded', 'false');
            this.isDropdownOpen = false;
        }
    }
    
    loadNotifications() {
        // Simulate loading from API
        setTimeout(() => {
            this.notifications = [
                {
                    id: 1,
                    type: 'urgent',
                    title: 'SLA Warning',
                    message: 'Claim CLM-2024-156 approaching deadline in 2 hours',
                    timestamp: new Date(Date.now() - 15 * 60 * 1000),
                    read: false,
                    actionUrl: '/insurance/assessments/CLM-2024-156'
                },
                {
                    id: 2,
                    type: 'urgent',
                    title: 'High Priority Claim',
                    message: 'Total loss assessment required for BMW X5',
                    timestamp: new Date(Date.now() - 45 * 60 * 1000),
                    read: false,
                    actionUrl: '/insurance/assessments/CLM-2024-201'
                },
                {
                    id: 3,
                    type: 'warning',
                    title: 'Document Missing',
                    message: 'Police report missing for claim CLM-2024-189',
                    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
                    read: false,
                    actionUrl: '/insurance/assessments/CLM-2024-189'
                },
                {
                    id: 4,
                    type: 'info',
                    title: 'New Assessment Request',
                    message: 'Assessment request received for Honda Civic',
                    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
                    read: false,
                    actionUrl: '/insurance/book-assessment'
                },
                {
                    id: 5,
                    type: 'success',
                    title: 'Assessment Completed',
                    message: 'CLM-2024-178 assessment completed successfully',
                    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
                    read: true,
                    actionUrl: '/insurance/assessments/CLM-2024-178'
                },
                {
                    id: 6,
                    type: 'info',
                    title: 'System Update',
                    message: 'New features available in assessment dashboard',
                    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
                    read: true,
                    actionUrl: '/insurance/assessments'
                }
            ];
            
            this.updateNotificationDisplay();
        }, 1000);
    }
    
    updateNotificationDisplay() {
        this.updateBadge();
        this.renderNotificationList();
    }
    
    updateBadge() {
        const badge = document.getElementById('notificationBadge');
        this.unreadCount = this.notifications.filter(n => !n.read).length;
        const hasUrgent = this.notifications.some(n => !n.read && n.type === 'urgent');
        
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount.toString();
                badge.style.display = 'flex';
                badge.classList.toggle('has-urgent', hasUrgent);
            } else {
                badge.style.display = 'none';
                badge.classList.remove('has-urgent');
            }
        }
    }
    
    renderNotificationList() {
        const listContainer = document.getElementById('notificationList');
        if (!listContainer) return;
        
        if (this.notifications.length === 0) {
            listContainer.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-bell-slash notification-empty-icon"></i>
                    <p class="notification-empty-text">No notifications</p>
                </div>
            `;
            return;
        }
        
        // Sort notifications by timestamp (newest first)
        const sortedNotifications = [...this.notifications].sort((a, b) => b.timestamp - a.timestamp);
        
        listContainer.innerHTML = sortedNotifications.map(notification => 
            this.createNotificationHTML(notification)
        ).join('');
        
        // Bind click events to notification items
        listContainer.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = parseInt(item.getAttribute('data-id'));
                this.handleNotificationClick(notificationId);
            });
            
            // Make items focusable
            item.setAttribute('tabindex', '0');
            item.setAttribute('role', 'menuitem');
        });
    }
    
    createNotificationHTML(notification) {
        const timeAgo = this.formatTimeAgo(notification.timestamp);
        const iconClass = this.getNotificationIcon(notification.type);
        
        return `
            <div class="notification-item ${notification.read ? '' : 'unread'} ${notification.type}" 
                 data-id="${notification.id}"
                 role="menuitem"
                 tabindex="0">
                <div class="notification-content">
                    <div class="notification-icon ${notification.type}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="notification-text">
                        <h4 class="notification-text-title">${notification.title}</h4>
                        <p class="notification-text-message">${notification.message}</p>
                        <p class="notification-text-time">${timeAgo}</p>
                    </div>
                </div>
                ${!notification.read ? '<div class="notification-unread-dot"></div>' : ''}
            </div>
        `;
    }
    
    getNotificationIcon(type) {
        const icons = {
            urgent: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle'
        };
        return icons[type] || icons.info;
    }
    
    formatTimeAgo(timestamp) {
        const now = new Date();
        const diff = now - timestamp;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return timestamp.toLocaleDateString();
    }
    
    handleNotificationClick(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;
        
        // Mark as read
        if (!notification.read) {
            this.markAsRead(notificationId);
        }
        
        // Navigate to action URL
        if (notification.actionUrl) {
            window.location.href = notification.actionUrl;
        }
        
        this.closeDropdown();
    }
    
    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.updateNotificationDisplay();
            
            // Simulate API call to mark as read
            this.sendReadStatus(notificationId);
        }
    }
    
    markAllAsRead() {
        const unreadNotifications = this.notifications.filter(n => !n.read);
        if (unreadNotifications.length === 0) return;
        
        unreadNotifications.forEach(notification => {
            notification.read = true;
        });
        
        this.updateNotificationDisplay();
        
        // Simulate API call
        this.sendBulkReadStatus(unreadNotifications.map(n => n.id));
        
        // Show feedback
        this.showToast('All notifications marked as read', 'success');
    }
    
    addNotification(notification) {
        // Add new notification to the beginning of the array
        this.notifications.unshift({
            id: Date.now(),
            timestamp: new Date(),
            read: false,
            ...notification
        });
        
        this.updateNotificationDisplay();
        
        // Play sound if enabled
        if (this.soundEnabled && notification.type === 'urgent') {
            this.playNotificationSound();
        }
        
        // Show browser notification if permission granted
        this.showBrowserNotification(notification);
    }
    
    removeNotification(notificationId) {
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
        this.updateNotificationDisplay();
    }
    
    startPeriodicUpdates() {
        // Check for new notifications every 30 seconds
        this.updateInterval = setInterval(() => {
            this.checkForNewNotifications();
        }, 30000);
    }
    
    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    checkForNewNotifications() {
        // Simulate checking for new notifications from server
        // In a real implementation, this would make an API call
        const shouldAddNew = Math.random() < 0.1; // 10% chance
        
        if (shouldAddNew) {
            const newNotification = this.generateRandomNotification();
            this.addNotification(newNotification);
        }
    }
    
    generateRandomNotification() {
        const types = ['info', 'warning', 'urgent'];
        const titles = [
            'New Assessment Request',
            'SLA Warning',
            'Document Uploaded',
            'Assessment Completed',
            'System Alert'
        ];
        const messages = [
            'A new vehicle assessment has been requested',
            'Claim approaching deadline',
            'New documents have been uploaded',
            'Assessment has been completed successfully',
            'System maintenance scheduled'
        ];
        
        const randomType = types[Math.floor(Math.random() * types.length)];
        const randomTitle = titles[Math.floor(Math.random() * titles.length)];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        
        return {
            type: randomType,
            title: randomTitle,
            message: randomMessage,
            actionUrl: '/insurance/assessments'
        };
    }
    
    handleDropdownKeyboard(e) {
        const items = Array.from(document.querySelectorAll('.notification-item'));
        const currentIndex = items.findIndex(item => item === document.activeElement);
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % items.length;
                items[nextIndex]?.focus();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                const prevIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
                items[prevIndex]?.focus();
                break;
                
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (document.activeElement.classList.contains('notification-item')) {
                    document.activeElement.click();
                }
                break;
        }
    }
    
    openSettings() {
        // Open notification settings modal or page
        console.log('Opening notification settings...');
        // This would typically open a modal or navigate to settings page
    }
    
    playNotificationSound() {
        if (!this.soundEnabled) return;
        
        // Create and play notification sound
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
        audio.volume = 0.3;
        audio.play().catch(() => {
            // Ignore errors if audio can't be played
        });
    }
    
    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/notification-icon.png',
                tag: `notification-${notification.id}`
            });
        }
    }
    
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg text-white transition-all duration-300 transform translate-x-full`;
        
        const bgColors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };
        
        toast.classList.add(bgColors[type] || bgColors.info);
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    sendReadStatus(notificationId) {
        // Simulate API call to mark notification as read
        console.log(`Marking notification ${notificationId} as read`);
    }
    
    sendBulkReadStatus(notificationIds) {
        // Simulate API call to mark multiple notifications as read
        console.log(`Marking notifications as read:`, notificationIds);
    }
    
    destroy() {
        this.stopPeriodicUpdates();
        
        // Remove event listeners
        const bellBtn = document.getElementById('notificationBellBtn');
        if (bellBtn) {
            bellBtn.replaceWith(bellBtn.cloneNode(true));
        }
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.notificationSystem = new NotificationSystem();
    
    // Request notification permission
    window.notificationSystem.requestNotificationPermission();
});

// Export for external use
window.NotificationSystem = NotificationSystem;