/**
 * Real-time log viewer with WebSocket support and advanced filtering
 */
class RealTimeLogViewer {
    constructor() {
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.lastLogId = 0;
        this.logs = [];
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.initializeElements();
        this.bindEvents();
        this.loadInitialLogs();
        this.initializeWebSocket();
    }

    initializeElements() {
        this.logsContainer = document.getElementById('logsContainer');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.logLevelSelect = document.getElementById('logLevel');
        this.logSourceSelect = document.getElementById('logSource');
        this.searchInput = document.getElementById('searchTerm');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.autoRefreshBtn = document.getElementById('autoRefreshBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.logCount = document.getElementById('logCount');
        this.lastUpdate = document.getElementById('lastUpdate');
        this.errorCount = document.getElementById('errorCount');
        this.warningCount = document.getElementById('warningCount');
    }

    bindEvents() {
        this.refreshBtn.addEventListener('click', () => this.loadLogs());
        this.clearBtn.addEventListener('click', () => this.clearLogs());
        this.autoRefreshBtn.addEventListener('click', () => this.toggleAutoRefresh());
        
        if (this.exportBtn) {
            this.exportBtn.addEventListener('click', () => this.exportLogs());
        }
        
        this.logLevelSelect.addEventListener('change', () => this.filterLogs());
        this.logSourceSelect.addEventListener('change', () => this.filterLogs());
        this.searchInput.addEventListener('input', this.debounce(() => this.filterLogs(), 300));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.loadLogs();
                        break;
                    case 'k':
                        e.preventDefault();
                        this.clearLogs();
                        break;
                    case 'f':
                        e.preventDefault();
                        this.searchInput.focus();
                        break;
                }
            }
        });
        
        // Auto-scroll toggle
        this.logsContainer.addEventListener('scroll', () => {
            const isAtBottom = this.logsContainer.scrollTop + this.logsContainer.clientHeight >= 
                              this.logsContainer.scrollHeight - 10;
            this.autoScroll = isAtBottom;
        });
    }

    initializeWebSocket() {
        if (!window.WebSocket) {
            console.warn('WebSocket not supported, falling back to polling');
            return;
        }

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/logs/`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('Connected (Real-time)', true);
                this.reconnectAttempts = 0;
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'log_entry') {
                        this.addNewLog(data.log);
                    } else if (data.type === 'log_batch') {
                        this.addNewLogs(data.logs);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('Disconnected', false);
                this.attemptReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('Connection Error', false);
            };
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.fallbackToPolling();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.initializeWebSocket();
            }, delay);
        } else {
            console.log('Max reconnection attempts reached, falling back to polling');
            this.fallbackToPolling();
        }
    }

    fallbackToPolling() {
        this.updateConnectionStatus('Polling Mode', true);
        if (!this.autoRefresh) {
            this.toggleAutoRefresh();
        }
    }

    async loadInitialLogs() {
        await this.loadLogs();
        this.updateStats();
    }

    async loadLogs() {
        try {
            this.updateConnectionStatus('Loading...', false);
            
            const params = new URLSearchParams({
                since: this.lastLogId,
                level: this.logLevelSelect.value,
                source: this.logSourceSelect.value,
                search: this.searchInput.value,
                limit: 100
            });

            const response = await fetch(`/insurance/api/logs/?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success && data.logs && data.logs.length > 0) {
                this.addNewLogs(data.logs);
            }
            
            this.updateConnectionStatus(
                this.websocket && this.websocket.readyState === WebSocket.OPEN 
                    ? 'Connected (Real-time)' 
                    : 'Connected', 
                true
            );
            this.updateLastUpdate();
            
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.updateConnectionStatus('Connection Error', false);
            this.showError(`Failed to load logs: ${error.message}`);
        }
    }

    addNewLog(log) {
        this.logs.unshift(log);
        this.lastLogId = Math.max(this.lastLogId, log.id);
        
        // Keep only last 1000 logs in memory
        if (this.logs.length > 1000) {
            this.logs = this.logs.slice(0, 1000);
        }
        
        this.renderLogs();
        this.updateStats();
        
        // Show notification for errors
        if (log.level === 'ERROR' || log.level === 'CRITICAL') {
            this.showNotification(`${log.level}: ${log.message}`, 'error');
        }
    }

    addNewLogs(logs) {
        if (!logs || logs.length === 0) return;
        
        // Sort logs by timestamp (newest first)
        logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        this.logs = [...logs, ...this.logs];
        this.lastLogId = Math.max(this.lastLogId, ...logs.map(log => log.id));
        
        // Keep only last 1000 logs in memory
        if (this.logs.length > 1000) {
            this.logs = this.logs.slice(0, 1000);
        }
        
        this.renderLogs();
        this.updateStats();
    }

    renderLogs() {
        this.loadingIndicator.style.display = 'none';
        
        const filteredLogs = this.getFilteredLogs();
        
        if (filteredLogs.length === 0) {
            this.logsContainer.innerHTML = '<div class="no-logs">No logs available</div>';
            this.updateLogCount(0);
            return;
        }

        // Use document fragment for better performance
        const fragment = document.createDocumentFragment();
        
        filteredLogs.forEach(log => {
            const logElement = this.createLogElement(log);
            fragment.appendChild(logElement);
        });
        
        this.logsContainer.innerHTML = '';
        this.logsContainer.appendChild(fragment);
        
        this.updateLogCount(filteredLogs.length);
        
        // Auto-scroll to bottom for new logs if user was at bottom
        if (this.autoScroll !== false) {
            this.logsContainer.scrollTop = this.logsContainer.scrollHeight;
        }
    }

    createLogElement(log) {
        const logEntry = document.createElement('div');
        const timestamp = new Date(log.timestamp).toLocaleString();
        const levelClass = log.level.toLowerCase();
        
        logEntry.className = `log-entry ${levelClass}`;
        logEntry.setAttribute('data-level', log.level);
        logEntry.setAttribute('data-source', log.source);
        logEntry.setAttribute('data-log-id', log.id);
        
        let detailsHtml = '';
        if (log.details && Object.keys(log.details).length > 0) {
            const detailsJson = JSON.stringify(log.details, null, 2);
            detailsHtml = `<div class="log-details" style="display: none;">${this.escapeHtml(detailsJson)}</div>`;
        }

        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            <span class="log-level ${log.level}">${log.level}</span>
            <span class="log-user">${log.user || 'System'}</span>
            <span class="log-message">${this.escapeHtml(log.message)}</span>
            ${detailsHtml}
        `;
        
        // Add click handler to toggle details
        if (detailsHtml) {
            logEntry.style.cursor = 'pointer';
            logEntry.addEventListener('click', () => {
                const details = logEntry.querySelector('.log-details');
                if (details) {
                    details.style.display = details.style.display === 'none' ? 'block' : 'none';
                }
            });
        }
        
        return logEntry;
    }

    getFilteredLogs() {
        return this.logs.filter(log => {
            const levelMatch = !this.logLevelSelect.value || log.level === this.logLevelSelect.value;
            const sourceMatch = !this.logSourceSelect.value || log.source.includes(this.logSourceSelect.value);
            const searchMatch = !this.searchInput.value || 
                log.message.toLowerCase().includes(this.searchInput.value.toLowerCase()) ||
                log.source.toLowerCase().includes(this.searchInput.value.toLowerCase()) ||
                (log.user && log.user.toLowerCase().includes(this.searchInput.value.toLowerCase()));
            
            return levelMatch && sourceMatch && searchMatch;
        });
    }

    filterLogs() {
        this.renderLogs();
    }

    clearLogs() {
        if (confirm('Are you sure you want to clear all logs from the display?')) {
            this.logs = [];
            this.lastLogId = 0;
            this.logsContainer.innerHTML = '<div class="no-logs">Logs cleared</div>';
            this.updateLogCount(0);
            this.updateStats();
        }
    }

    toggleAutoRefresh() {
        this.autoRefresh = !this.autoRefresh;
        
        if (this.autoRefresh) {
            this.autoRefreshBtn.textContent = 'Auto Refresh: ON';
            this.autoRefreshBtn.classList.add('active');
            this.refreshInterval = setInterval(() => this.loadLogs(), 5000);
        } else {
            this.autoRefreshBtn.textContent = 'Auto Refresh: OFF';
            this.autoRefreshBtn.classList.remove('active');
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        }
    }

    async exportLogs() {
        try {
            const params = new URLSearchParams({
                level: this.logLevelSelect.value,
                days: 7
            });
            
            const response = await fetch(`/insurance/api/logs/export/?${params}`);
            
            if (!response.ok) {
                throw new Error(`Export failed: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `logs_export_${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Logs exported successfully', 'success');
            
        } catch (error) {
            console.error('Export failed:', error);
            this.showError(`Export failed: ${error.message}`);
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/insurance/api/logs/stats/');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                if (this.errorCount) {
                    this.errorCount.textContent = stats.by_severity.error + stats.by_severity.critical;
                }
                
                if (this.warningCount) {
                    this.warningCount.textContent = stats.by_severity.warning;
                }
            }
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    updateConnectionStatus(status, connected) {
        this.connectionStatus.textContent = status;
        const statusDot = document.querySelector('.status-dot');
        if (statusDot) {
            statusDot.style.backgroundColor = connected ? '#18cb96' : '#e74c3c';
            statusDot.style.animationPlayState = connected ? 'running' : 'paused';
        }
    }

    updateLogCount(count) {
        this.logCount.textContent = `${count} log${count !== 1 ? 's' : ''}`;
    }

    updateLastUpdate() {
        this.lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        // Remove existing notifications of the same type
        const existing = document.querySelectorAll(`.notification-${type}`);
        existing.forEach(n => n.remove());
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

    destroy() {
        if (this.websocket) {
            this.websocket.close();
        }
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.logViewer = new RealTimeLogViewer();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.logViewer) {
        window.logViewer.destroy();
    }
});