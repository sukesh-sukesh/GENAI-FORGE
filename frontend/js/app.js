/**
 * InsureGuard AI - Main Application Router
 * Handles navigation and page routing.
 */

const App = {
    currentPage: null,

    /**
     * Initialize the application.
     */
    init() {
        if (!Auth.isLoggedIn()) {
            this.navigate('login');
        } else {
            this.navigate('dashboard');
        }
    },

    /**
     * Navigate to a page.
     */
    navigate(page) {
        this.currentPage = page;

        // Remove any open modals
        document.querySelectorAll('.modal-overlay').forEach(m => m.remove());

        switch (page) {
            case 'login':
                Auth.renderAuthPage();
                break;

            case 'dashboard':
                Dashboard.render();
                break;

            case 'new-claim':
                Claims.renderNewClaimForm();
                break;

            case 'my-claims':
                Claims.renderClaimsList('My Claims');
                break;

            case 'claims-list':
                Claims.renderClaimsList('All Claims');
                break;

            case 'analytics':
                Admin.renderAnalytics();
                break;

            case 'alerts':
                Admin.renderAlerts();
                break;

            case 'fraud-intel':
                Manager.renderFraudIntelligence();
                break;

            case 'ml-insights':
                Admin.renderMlInsights();
                break;

            case 'fraud-network':
                Admin.renderFraudNetwork();
                break;

            case 'high-risk':
                Manager.renderHighRiskClaims();
                break;

            case 'audit-logs':
                Admin.renderAuditLogs();
                break;

            case 'settings':
                Admin.renderSettings();
                break;

            default:
                this.navigate('dashboard');
        }
    },
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
