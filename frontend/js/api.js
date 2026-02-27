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
        return this.request('/admin/risk-threshold');
    },

    async updateThresholds(fraud_threshold, avg_fraud_loss = null) {
        let url = `/admin/risk-threshold?fraud_threshold=${fraud_threshold}`;
        if (avg_fraud_loss) {
            url += `&avg_fraud_loss=${avg_fraud_loss}`;
        }
        return this.request(url, {
            method: 'PUT',
        });
    },

    async getBusinessImpact() {
        return this.request('/admin/business-impact');
    },

    async getFraudNetwork() {
        return this.request('/admin/fraud-network');
    },

    async getTimeline() {
        return this.request('/admin/timeline');
    },

    async getMlMetrics() {
        return this.request('/admin/ml-metrics');
    },

    async downloadReport(claimId) {
        const token = localStorage.getItem(CONFIG.TOKEN_KEY);
        // Better way to download: fetch and create blob URL so we can pass Bearer token in headers
        const response = await fetch(`${CONFIG.API_BASE}/claims/${claimId}/report`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("Failed to download report");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Claim_${claimId}_Report.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    async labelClaim(claimId, label) {
        return this.request(`/claims/${claimId}/label?label=${label}`, {
            method: 'POST',
        });
    }
};
