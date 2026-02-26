/**
 * InsureGuard AI - API Service
 * Handles all HTTP communication with the backend.
 */

const API = {
    /**
     * Make an authenticated API request.
     */
    async request(endpoint, options = {}) {
        const token = localStorage.getItem(CONFIG.TOKEN_KEY);
        const headers = {
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Don't set Content-Type for FormData (file uploads)
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
                ...options,
                headers,
            });

            if (response.status === 401) {
                // Token expired — logout
                Auth.logout();
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                showToast('Cannot connect to server. Please ensure the backend is running.', 'error');
            }
            throw error;
        }
    },

    // Auth
    async login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    },

    async getProfile() {
        return this.request('/auth/me');
    },

    // Claims
    async submitClaim(claimData) {
        return this.request('/claims/', {
            method: 'POST',
            body: JSON.stringify(claimData),
        });
    },

    async getClaims(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/claims/?${query}`);
    },

    async getClaim(id) {
        return this.request(`/claims/${id}`);
    },

    async updateClaim(id, data) {
        return this.request(`/claims/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    async predictRisk(id) {
        return this.request(`/claims/${id}/predict`, {
            method: 'POST',
        });
    },

    // Analytics
    async getAnalytics() {
        return this.request('/claims/analytics');
    },

    // Documents
    async uploadDocument(claimId, documentType, file) {
        const formData = new FormData();
        formData.append('claim_id', claimId);
        formData.append('document_type', documentType);
        formData.append('file', file);

        return this.request('/documents/upload', {
            method: 'POST',
            body: formData,
        });
    },

    async getClaimDocuments(claimId) {
        return this.request(`/documents/claim/${claimId}`);
    },

    async checkDocuments(claimId, category) {
        return this.request(`/documents/check/${claimId}/${category}`);
    },

    // Admin
    async getFraudIntelligence() {
        return this.request('/admin/fraud-intelligence');
    },

    async getAlerts() {
        return this.request('/admin/alerts');
    },

    async getHighRiskClaims() {
        return this.request('/admin/high-risk-claims');
    },

    async getAuditLogs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/audit-logs?${query}`);
    },

    async getThresholds() {
        return this.request('/admin/thresholds');
    },

    async updateThresholds(low, high) {
        return this.request(`/admin/thresholds?low=${low}&high=${high}`, {
            method: 'POST',
        });
    },
};
