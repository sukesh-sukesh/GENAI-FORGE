/**
 * InsureGuard AI - Reusable UI Components
 * Shared components used across all pages.
 */

/**
 * Show a toast notification.
 */
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

  toast.innerHTML = `
    <span>${icons[type] || 'ℹ️'}</span>
    <span style="flex:1">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Format currency in Indian Rupees.
 */
function formatCurrency(amount) {
  if (!amount && amount !== 0) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format date to a readable string.
 */
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

/**
 * Format date with time.
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/**
 * Render a risk badge.
 */
function renderRiskBadge(risk) {
  if (!risk) return '<span class="badge badge-pending">Unknown</span>';
  const labels = { low: '🟢 Low', medium: '🟡 Medium', high: '🔴 High' };
  return `<span class="badge badge-${risk}">${labels[risk] || risk}</span>`;
}

/**
 * Render a status badge.
 */
function renderStatusBadge(status) {
  if (!status) return '';
  const icons = {
    pending: '⏳', under_review: '🔍', approved: '✅',
    rejected: '❌', escalated: '🚨'
  };
  const label = CONFIG.STATUS_LABELS[status] || status;
  return `<span class="badge badge-${status}">${icons[status] || ''} ${label}</span>`;
}

/**
 * Render a category badge.
 */
function renderCategoryBadge(category) {
  if (!category) return '';
  const info = CONFIG.INSURANCE_CATEGORIES[category];
  return `<span class="badge badge-${category}">${info?.icon || ''} ${info?.label || category}</span>`;
}

/**
 * Render a risk progress bar.
 */
function renderRiskBar(score) {
  if (score === null || score === undefined) return '';
  const riskClass = score < 30 ? 'low' : score < 70 ? 'medium' : 'high';
  return `
    <div style="display: flex; align-items: center; gap: 8px;">
      <div class="risk-bar">
        <div class="risk-bar-fill ${riskClass}" style="width: ${score}%"></div>
      </div>
      <span style="font-size: 0.85rem; font-weight: 600;">${score.toFixed(1)}%</span>
    </div>
  `;
}

/**
 * Render the sidebar navigation.
 */
function renderSidebar(activePage) {
  const user = Auth.getUser();
  const role = user?.role || 'user';

  const navItems = {
    user: [
      { id: 'dashboard', icon: '📊', label: 'Dashboard' },
      { id: 'new-claim', icon: '📝', label: 'File New Claim' },
      { id: 'my-claims', icon: '📋', label: 'My Claims' },
    ],
    agent: [
      { id: 'dashboard', icon: '📊', label: 'Dashboard' },
      { id: 'claims-list', icon: '📋', label: 'All Claims' },
      { id: 'analytics', icon: '📈', label: 'Analytics' },
      { id: 'alerts', icon: '🔔', label: 'Alerts' },
    ],
    manager: [
      { id: 'dashboard', icon: '📊', label: 'Dashboard' },
      { id: 'claims-list', icon: '📋', label: 'All Claims' },
      { id: 'analytics', icon: '📈', label: 'Analytics' },
      { id: 'ml-insights', icon: '🧠', label: 'ML Insights' },
      { id: 'fraud-network', icon: '🕸️', label: 'Fraud Network' },
      { id: 'fraud-intel', icon: '🕵️', label: 'Fraud Intelligence' },
      { id: 'alerts', icon: '🔔', label: 'Alerts' },
      { id: 'high-risk', icon: '🚨', label: 'High Risk Claims' },
      { id: 'audit-logs', icon: '📜', label: 'Audit Logs' },
      { id: 'settings', icon: '⚙️', label: 'Settings' },
    ],
  };

  const items = navItems[role] || navItems.user;
  const initials = (user?.full_name || 'U').split(' ').map(n => n[0]).join('').toUpperCase();

  return `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">🛡️</div>
        <div class="sidebar-brand">
          <h2>InsureGuard</h2>
          <span>AI Fraud Detection</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title">Main Menu</div>
          ${items.map(item => `
            <button class="nav-item ${activePage === item.id ? 'active' : ''}"
                    onclick="App.navigate('${item.id}')">
              <span class="icon">${item.icon}</span>
              <span>${item.label}</span>
            </button>
          `).join('')}
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">${initials}</div>
          <div class="user-details">
            <div class="name">${user?.full_name || 'User'}</div>
            <div class="role">${role}</div>
          </div>
          <button class="logout-btn" onclick="Auth.logout()" title="Sign Out">↗️</button>
        </div>
      </div>
    </aside>
  `;
}

/**
 * Render page layout with sidebar.
 */
function renderPageLayout(activePage, content) {
  return `
    <div class="dashboard-layout">
      ${renderSidebar(activePage)}
      <main class="main-content" style="position: relative;">
        <div style="position: absolute; top: 16px; right: 24px; z-index: 10;">
          <button class="btn btn-primary btn-sm" onclick="Auth.logout()" style="display: flex; align-items: center; gap: 8px;">
            Logout ↗️
          </button>
        </div>
        <button class="mobile-menu-btn" onclick="toggleSidebar()">☰</button>
        ${content}
      </main>
    </div>
  `;
}

function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('open');
}

/**
 * Render a loading state.
 */
function renderLoading() {
  return `
    <div class="loading-spinner">
      <div class="spinner"></div>
    </div>
  `;
}

/**
 * Render an empty state.
 */
function renderEmptyState(icon, message) {
  return `
    <div class="empty-state">
      <div class="icon">${icon}</div>
      <p>${message}</p>
    </div>
  `;
}

/**
 * Debounce function for search.
 */
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
