/**
 * Assessment Comments and Feedback System
 * Handles comment threading, notifications, and real-time updates
 */

class AssessmentCommentSystem {
    constructor(assessmentId) {
        this.assessmentId = assessmentId;
        this.init();
    }

    init() {
        this.loadComments();
        this.setupEventListeners();
        this.loadNotifications();
        this.setupNotificationPolling();
    }

    setupEventListeners() {
        // Reply form toggles
        document.addEventListener('click', (e) => {
            if (e.target.matches('.reply-toggle')) {
                e.preventDefault();
                this.toggleReplyForm(e.target);
            }
        });

        // Resolve comment buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.resolve-comment')) {
                e.preventDefault();
                this.resolveComment(e.target);
            }
        });

        // Reply form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.reply-form')) {
                e.preventDefault();
                this.submitReply(e.target);
            }
        });

        // Notification clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.notification-item')) {
                this.markNotificationAsRead(e.target);
            }
        });
    }

    async loadComments() {
        try {
            const response = await fetch(`/insurance/api/assessments/${this.assessmentId}/comments/`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderComments(data.comments);
                this.updateCommentCount(data.total_comments);
            } else {
                console.error('Failed to load comments:', data);
            }
        } catch (error) {
            console.error('Error loading comments:', error);
        }
    }

    renderComments(comments) {
        const container = document.getElementById('comments-container');
        if (!container) return;

        if (comments.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.013 8.013 0 01-2.5-.4l-3.5 2.4v-2.8A8 8 0 1121 12z"></path>
                    </svg>
                    <p>No comments yet. Be the first to add feedback!</p>
                </div>
            `;
            return;
        }

        const html = comments.map(comment => this.renderCommentCard(comment)).join('');
        container.innerHTML = html;
    }

    renderCommentCard(comment) {
        const commentHtml = `
            <div class="comment-card mb-6 bg-white rounded-lg shadow-sm border border-gray-200">
                <div class="p-4">
                    ${this.renderComment(comment, true)}
                    
                    <div class="reply-form-container mt-4" id="reply-form-${comment.id}" style="display: none;">
                        <form class="reply-form" data-parent-id="${comment.id}">
                            <div class="flex space-x-3">
                                <div class="flex-1">
                                    <textarea name="content" rows="3" 
                                              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                              placeholder="Write your reply..."></textarea>
                                </div>
                                <div class="flex flex-col space-y-2">
                                    <button type="submit" 
                                            class="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                                        Reply
                                    </button>
                                    <button type="button" 
                                            class="px-3 py-2 bg-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-400 focus:outline-none"
                                            onclick="this.closest('.reply-form-container').style.display='none'">
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        return commentHtml;
    }

    renderComment(comment, isParent = false) {
        const typeColors = {
            'Internal Note': 'bg-gray-100 text-gray-800',
            'Customer Communication': 'bg-blue-100 text-blue-800',
            'Adjuster Note': 'bg-purple-100 text-purple-800',
            'Repair Shop Input': 'bg-green-100 text-green-800',
            'Expert Opinion': 'bg-yellow-100 text-yellow-800',
            'Dispute Resolution': 'bg-red-100 text-red-800'
        };

        const typeColor = typeColors[comment.comment_type] || 'bg-gray-100 text-gray-800';
        const importantBadge = comment.is_important ? 
            `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 ml-2">
                <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                Important
            </span>` : '';

        const actionRequired = comment.requires_action ?
            `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 ml-2">
                Action Required
            </span>` : '';

        const customerVisible = comment.is_customer_visible ?
            `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 ml-2">
                Customer Visible
            </span>` : '';

        return `
            <div class="comment ${isParent ? 'parent-comment' : 'reply-comment'}">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                            ${comment.author.charAt(0).toUpperCase()}
                        </div>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2 mb-1">
                            <p class="text-sm font-medium text-gray-900">${comment.author}</p>
                            ${isParent ? `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${typeColor}">${comment.comment_type}</span>` : ''}
                            ${importantBadge}
                            ${actionRequired}
                            ${customerVisible}
                        </div>
                        <p class="text-sm text-gray-500 mb-2">${this.formatDate(comment.created_at)}</p>
                        ${comment.subject ? `<p class="text-sm font-medium text-gray-900 mb-1">${comment.subject}</p>` : ''}
                        <div class="text-sm text-gray-900 whitespace-pre-wrap">${comment.content}</div>
                        
                        <div class="mt-3 flex items-center space-x-4">
                            <button class="reply-toggle text-sm text-blue-600 hover:text-blue-800" data-comment-id="${comment.id}">
                                Reply
                            </button>
                            ${comment.requires_action ? `
                                <button class="resolve-comment text-sm text-green-600 hover:text-green-800" data-comment-id="${comment.id}">
                                    Mark as Resolved
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    toggleReplyForm(button) {
        const commentId = button.dataset.commentId;
        const replyForm = document.getElementById(`reply-form-${commentId}`);
        
        if (replyForm) {
            replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
            if (replyForm.style.display === 'block') {
                const textarea = replyForm.querySelector('textarea');
                if (textarea) textarea.focus();
            }
        }
    }

    async submitReply(form) {
        const parentId = form.dataset.parentId;
        const content = form.querySelector('textarea[name="content"]').value.trim();
        
        if (!content) {
            alert('Please enter a reply message.');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('content', content);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(`/insurance/assessments/${this.assessmentId}/comments/${parentId}/reply/`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Reload comments to show the new reply
                await this.loadComments();
                form.reset();
                form.closest('.reply-form-container').style.display = 'none';
                this.showNotification('Reply added successfully!', 'success');
            } else {
                this.showNotification('Error adding reply. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error submitting reply:', error);
            this.showNotification('Error adding reply. Please try again.', 'error');
        }
    }

    async resolveComment(button) {
        const commentId = button.dataset.commentId;
        
        if (!confirm('Are you sure you want to mark this comment as resolved?')) {
            return;
        }

        try {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(`/insurance/assessments/${this.assessmentId}/comments/${commentId}/resolve/`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                await this.loadComments();
                this.showNotification('Comment marked as resolved!', 'success');
            } else {
                this.showNotification('Error resolving comment. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error resolving comment:', error);
            this.showNotification('Error resolving comment. Please try again.', 'error');
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/insurance/api/notifications/');
            const data = await response.json();
            
            if (response.ok) {
                this.renderNotifications(data.notifications);
                this.updateNotificationBadge(data.unread_count);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    renderNotifications(notifications) {
        const container = document.getElementById('notifications-container');
        if (!container) return;

        if (notifications.length === 0) {
            container.innerHTML = '<div class="p-4 text-center text-gray-500">No notifications</div>';
            return;
        }

        const html = notifications.map(notification => `
            <div class="notification-item p-4 border-b border-gray-200 hover:bg-gray-50 cursor-pointer ${notification.status === 'unread' ? 'bg-blue-50' : ''}"
                 data-notification-id="${notification.id}">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        ${notification.status === 'unread' ? '<div class="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>' : '<div class="w-2 h-2 mt-2"></div>'}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900">${notification.title}</p>
                        <p class="text-sm text-gray-600 mt-1">${notification.message}</p>
                        <p class="text-xs text-gray-500 mt-1">${this.formatDate(notification.created_at)}</p>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    async markNotificationAsRead(element) {
        const notificationId = element.dataset.notificationId;
        
        try {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(`/insurance/api/notifications/${notificationId}/read/`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                element.classList.remove('bg-blue-50');
                const unreadDot = element.querySelector('.bg-blue-500');
                if (unreadDot) {
                    unreadDot.classList.remove('bg-blue-500');
                }
                this.loadNotifications(); // Refresh to update badge count
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    updateCommentCount(count) {
        const counter = document.getElementById('comment-count');
        if (counter) {
            counter.textContent = count;
        }
    }

    setupNotificationPolling() {
        // Poll for new notifications every 30 seconds
        setInterval(() => {
            this.loadNotifications();
        }, 30000);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    showNotification(message, type = 'info') {
        // Create a temporary notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-md shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize the comment system when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const assessmentId = document.querySelector('[data-assessment-id]')?.dataset.assessmentId;
    if (assessmentId) {
        window.commentSystem = new AssessmentCommentSystem(assessmentId);
    }
});