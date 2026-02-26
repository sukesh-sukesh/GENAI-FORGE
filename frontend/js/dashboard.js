/**
 * InsureGuard AI - Dashboard Module
 * Main dashboard rendering for all user roles.
 */

const Dashboard = {
    chartInstances: {},

    /**
     * Render the dashboard page.
     */
    async render() {
        const user = Auth.getUser();
        const role = user?.role || 'user';

        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('dashboard', `
      <div class="top-bar">
        <div class="page-title">
          <h1>Welcome, ${user?.full_name?.split(' ')[0] || 'User'} 👋</h1>
          <p>${role === 'manager' ? 'Manager Dashboard — Complete fraud oversight' :
                role === 'agent' ? 'Agent Dashboard — Review and process claims' :
                    'Your insurance claims dashboard'}</p>
        </div>
      </div>
      <div id="dashboard-content">${renderLoading()}</div>
    `);

        if (role === 'user') {
            await this.renderUserDashboard();
        } else {
            await this.renderStaffDashboard(role);
        }
    },

    /**
     * Render user (policyholder) dashboard.
     */
    async renderUserDashboard() {
        try {
            const data = await API.getClaims({ page: 1, page_size: 10 });
            const claims = data?.claims || [];
            const total = data?.total || 0;

            const pending = claims.filter(c => c.status === 'pending').length;
            const approved = claims.filter(c => c.status === 'approved').length;

            document.getElementById('dashboard-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card blue">
            <div class="stat-card-header">
              <div class="stat-card-icon">📋</div>
              <span class="stat-card-label">Total Claims</span>
            </div>
            <div class="stat-card-value">${total}</div>
          </div>
          <div class="stat-card amber">
            <div class="stat-card-header">
              <div class="stat-card-icon">⏳</div>
              <span class="stat-card-label">Pending</span>
            </div>
            <div class="stat-card-value">${pending}</div>
          </div>
          <div class="stat-card green">
            <div class="stat-card-header">
              <div class="stat-card-icon">✅</div>
              <span class="stat-card-label">Approved</span>
            </div>
            <div class="stat-card-value">${approved}</div>
          </div>
        </div>

        <div class="glass-card">
          <div class="card-header">
            <h3>📋 Recent Claims</h3>
            <button class="btn btn-primary btn-sm" onclick="App.navigate('new-claim')">
              + File New Claim
            </button>
          </div>
          ${claims.length > 0 ? `
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Claim #</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  ${claims.map(c => `
                    <tr onclick="Claims.showDetail(${c.id})" style="cursor:pointer">
                      <td><strong>${c.claim_number}</strong></td>
                      <td>${renderCategoryBadge(c.insurance_category)}</td>
                      <td>${formatCurrency(c.claim_amount)}</td>
                      <td>${renderStatusBadge(c.status)}</td>
                      <td>${renderRiskBar(c.risk_score)}</td>
                      <td>${formatDate(c.created_at)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : renderEmptyState('📋', 'No claims yet. File your first claim!')}
        </div>
      `;
        } catch (error) {
            document.getElementById('dashboard-content').innerHTML =
                renderEmptyState('❌', 'Failed to load dashboard data');
        }
    },

    /**
     * Render staff (agent/manager) dashboard.
     */
    async renderStaffDashboard(role) {
        try {
            const analytics = await API.getAnalytics();

            document.getElementById('dashboard-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card blue">
            <div class="stat-card-header">
              <div class="stat-card-icon">📋</div>
              <span class="stat-card-label">Total Claims</span>
            </div>
            <div class="stat-card-value">${analytics.total_claims}</div>
          </div>
          <div class="stat-card amber">
            <div class="stat-card-header">
              <div class="stat-card-icon">⏳</div>
              <span class="stat-card-label">Pending Review</span>
            </div>
            <div class="stat-card-value">${analytics.pending_claims}</div>
          </div>
          <div class="stat-card red">
            <div class="stat-card-header">
              <div class="stat-card-icon">🚨</div>
              <span class="stat-card-label">High Risk</span>
            </div>
            <div class="stat-card-value">${analytics.high_risk_claims}</div>
          </div>
          <div class="stat-card green">
            <div class="stat-card-header">
              <div class="stat-card-icon">📊</div>
              <span class="stat-card-label">Avg Fraud Score</span>
            </div>
            <div class="stat-card-value">${(analytics.average_fraud_probability * 100).toFixed(1)}%</div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="glass-card">
            <div class="card-header">
              <h3>📊 Claims by Status</h3>
            </div>
            <div class="chart-container">
              <canvas id="statusChart"></canvas>
            </div>
          </div>
          <div class="glass-card">
            <div class="card-header">
              <h3>📈 Claims by Category</h3>
            </div>
            <div class="chart-container">
              <canvas id="categoryChart"></canvas>
            </div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="glass-card">
            <div class="card-header">
              <h3>📉 Fraud Trend (30 Days)</h3>
            </div>
            <div class="chart-container">
              <canvas id="fraudTrendChart"></canvas>
            </div>
          </div>
          <div class="glass-card">
            <div class="card-header">
              <h3>🎯 Risk Distribution</h3>
            </div>
            <div class="chart-container">
              <canvas id="riskChart"></canvas>
            </div>
          </div>
        </div>

        <div class="glass-card">
          <div class="card-header">
            <h3>🕐 Recent Claims</h3>
            <button class="btn btn-ghost btn-sm" onclick="App.navigate('claims-list')">View All →</button>
          </div>
          ${analytics.recent_claims?.length > 0 ? `
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Claim #</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Fraud Score</th>
                    <th>Risk</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${analytics.recent_claims.map(c => `
                    <tr>
                      <td><strong>${c.claim_number}</strong></td>
                      <td>${renderCategoryBadge(c.insurance_category)}</td>
                      <td>${formatCurrency(c.claim_amount)}</td>
                      <td>${renderStatusBadge(c.status)}</td>
                      <td>${c.fraud_probability ? (c.fraud_probability * 100).toFixed(1) + '%' : '—'}</td>
                      <td>${renderRiskBadge(c.risk_category)}</td>
                      <td>${formatDate(c.created_at)}</td>
                      <td>
                        <button class="btn btn-ghost btn-sm" onclick="Claims.showDetail(${c.id})">
                          View
                        </button>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : renderEmptyState('📋', 'No claims data available')}
        </div>
      `;

            // Render charts
            this.renderCharts(analytics);
        } catch (error) {
            console.error('Dashboard error:', error);
            document.getElementById('dashboard-content').innerHTML =
                renderEmptyState('❌', 'Failed to load analytics. Make sure you have agent or manager access.');
        }
    },

    /**
     * Create dashboard charts.
     */
    renderCharts(analytics) {
        // Destroy existing chart instances
        Object.values(this.chartInstances).forEach(c => c?.destroy());

        const chartDefaults = {
            color: '#94a3b8',
            font: { family: 'Inter' },
        };

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Inter';

        // Status pie chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            this.chartInstances.status = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Pending', 'Under Review', 'Approved', 'Rejected', 'Escalated'],
                    datasets: [{
                        data: [
                            analytics.claims_by_status?.pending || 0,
                            analytics.claims_by_status?.under_review || 0,
                            analytics.claims_by_status?.approved || 0,
                            analytics.claims_by_status?.rejected || 0,
                            analytics.claims_by_status?.escalated || 0,
                        ],
                        backgroundColor: [
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(244, 63, 94, 0.8)',
                            'rgba(249, 115, 22, 0.8)',
                        ],
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: { position: 'bottom', labels: { padding: 16 } },
                    },
                },
            });
        }

        // Category bar chart
        const catCtx = document.getElementById('categoryChart');
        if (catCtx) {
            this.chartInstances.category = new Chart(catCtx, {
                type: 'bar',
                data: {
                    labels: ['Vehicle', 'Health', 'Property'],
                    datasets: [{
                        label: 'Claims',
                        data: [
                            analytics.claims_by_category?.vehicle || 0,
                            analytics.claims_by_category?.health || 0,
                            analytics.claims_by_category?.property || 0,
                        ],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.7)',
                            'rgba(16, 185, 129, 0.7)',
                            'rgba(139, 92, 246, 0.7)',
                        ],
                        borderRadius: 8,
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { stepSize: 1 }
                        },
                        x: { grid: { display: false } },
                    },
                },
            });
        }

        // Fraud trend line chart
        const trendCtx = document.getElementById('fraudTrendChart');
        if (trendCtx && analytics.fraud_trend?.length > 0) {
            this.chartInstances.trend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: analytics.fraud_trend.map(d => d.date),
                    datasets: [
                        {
                            label: 'Total Claims',
                            data: analytics.fraud_trend.map(d => d.total_claims),
                            borderColor: 'rgba(59, 130, 246, 0.8)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                        },
                        {
                            label: 'High Risk',
                            data: analytics.fraud_trend.map(d => d.high_risk_claims),
                            borderColor: 'rgba(244, 63, 94, 0.8)',
                            backgroundColor: 'rgba(244, 63, 94, 0.1)',
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { stepSize: 1 }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { maxRotation: 45 }
                        },
                    },
                },
            });
        }

        // Risk distribution chart
        const riskCtx = document.getElementById('riskChart');
        if (riskCtx) {
            this.chartInstances.risk = new Chart(riskCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Low Risk', 'Medium Risk', 'High Risk'],
                    datasets: [{
                        data: [
                            analytics.low_risk_claims || 0,
                            analytics.medium_risk_claims || 0,
                            analytics.high_risk_claims || 0,
                        ],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(244, 63, 94, 0.8)',
                        ],
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: { position: 'bottom', labels: { padding: 16 } },
                    },
                },
            });
        }
    },
};
