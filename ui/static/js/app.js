// JEECG A2A Platform - Main JavaScript Application

// Global application state
window.A2AApp = {
    version: '1.0.0',
    debug: false,
    apiBaseUrl: '/api',
    wsBaseUrl: 'ws://localhost:6000/ws',
    
    // Initialize the application
    init: function() {
        console.log('Initializing JEECG A2A Platform...');
        this.setupGlobalErrorHandling();
        this.setupTooltips();
        this.setupTheme();
        this.checkPlatformHealth();
    },
    
    // Setup global error handling
    setupGlobalErrorHandling: function() {
        window.addEventListener('error', function(e) {
            console.error('Global JavaScript error:', e.error);
            A2AApp.showNotification('An unexpected error occurred', 'error');
        });
        
        window.addEventListener('unhandledrejection', function(e) {
            console.error('Unhandled promise rejection:', e.reason);
            A2AApp.showNotification('An unexpected error occurred', 'error');
        });
    },
    
    // Setup Bootstrap tooltips
    setupTooltips: function() {
        if (typeof bootstrap !== 'undefined') {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    },
    
    // Setup theme management
    setupTheme: function() {
        const savedTheme = localStorage.getItem('a2a-theme') || 'light';
        this.setTheme(savedTheme);
    },
    
    // Set theme
    setTheme: function(theme) {
        document.body.setAttribute('data-bs-theme', theme);
        localStorage.setItem('a2a-theme', theme);
    },
    
    // Toggle theme
    toggleTheme: function() {
        const currentTheme = document.body.getAttribute('data-bs-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    },
    
    // Check platform health
    checkPlatformHealth: async function() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            if (health.status === 'healthy') {
                console.log('Platform is healthy');
            } else {
                console.warn('Platform health check failed:', health);
                this.showNotification('Platform health check failed', 'warning');
            }
        } catch (error) {
            console.error('Health check error:', error);
            this.showNotification('Unable to check platform health', 'error');
        }
    },
    
    // Show notification
    showNotification: function(message, type = 'info', duration = 5000) {
        const alertClass = {
            'info': 'alert-info',
            'success': 'alert-success',
            'warning': 'alert-warning',
            'error': 'alert-danger'
        }[type] || 'alert-info';
        
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const alerts = document.querySelectorAll('.alert');
                if (alerts.length > 0) {
                    const lastAlert = alerts[alerts.length - 1];
                    if (lastAlert && typeof bootstrap !== 'undefined') {
                        const alert = bootstrap.Alert.getOrCreateInstance(lastAlert);
                        alert.close();
                    }
                }
            }, duration);
        }
    },
    
    // Format timestamp
    formatTimestamp: function(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    },
    
    // Format duration
    formatDuration: function(seconds) {
        if (seconds < 60) {
            return `${seconds}s`;
        } else if (seconds < 3600) {
            return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    },
    
    // Copy to clipboard
    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard', 'success', 2000);
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            this.showNotification('Failed to copy to clipboard', 'error');
        }
    },
    
    // Download as JSON
    downloadAsJson: function(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // API helper methods
    api: {
        // Generic API call
        call: async function(endpoint, options = {}) {
            const url = A2AApp.apiBaseUrl + endpoint;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            const finalOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, finalOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API call failed:', error);
                throw error;
            }
        },
        
        // Get agents
        getAgents: async function() {
            return await this.call('/agents');
        },
        
        // Register agent
        registerAgent: async function(url) {
            return await this.call('/agents/register', {
                method: 'POST',
                body: JSON.stringify({ url })
            });
        },
        
        // Get tasks
        getTasks: async function() {
            return await this.call('/tasks');
        },
        
        // Submit task
        submitTask: async function(message, contextId = null, sessionId = null) {
            const taskRequest = {
                message: {
                    role: 'user',
                    parts: [{ type: 'text', content: message }]
                },
                context_id: contextId,
                session_id: sessionId
            };
            
            return await this.call('/tasks', {
                method: 'POST',
                body: JSON.stringify(taskRequest)
            });
        },
        
        // Get health
        getHealth: async function() {
            return await this.call('/health', { baseUrl: '' });
        }
    },
    
    // WebSocket helper
    createWebSocket: function(endpoint, onMessage, onError) {
        const wsUrl = this.wsBaseUrl + endpoint;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = function(event) {
            console.log('WebSocket connected:', endpoint);
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket disconnected:', endpoint);
        };
        
        return ws;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.A2AApp.init();
});

// Global utility functions
function showNotification(message, type, duration) {
    window.A2AApp.showNotification(message, type, duration);
}

function toggleTheme() {
    window.A2AApp.toggleTheme();
}

function copyToClipboard(text) {
    window.A2AApp.copyToClipboard(text);
}

function downloadAsJson(data, filename) {
    window.A2AApp.downloadAsJson(data, filename);
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.A2AApp;
}
