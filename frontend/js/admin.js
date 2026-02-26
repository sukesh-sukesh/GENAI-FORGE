/**
 * InsureGuard AI - Admin/Agent Module
 * Analytics, alerts, and audit log pages.
 */

const Admin = {
    chartInstances: {},

    async renderAnalytics() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('analytics', `
      <div class="top-bar">
        <div class="page-title">
          <h1>📈 Claim Analytics</h1>
          <p>Comprehensive fraud detection analytics</p>
        </div>
      </div>
      <div id="analytics-content">${renderLoading()}</div>
    `);

        try {
            const data = await API.getAnalytics();
            document.getElementById('analytics-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card blue">
            <div class="stat-card-header"><div class="stat-card-icon">📋</div><span class="stat-card-label">Total Claims</span></div>
            <div class="stat-card-value">${data.total_claims}</div>
          </div>
          <div class="stat-card green">
            <div class="stat-card-header"><div class="stat-card-icon">✅</div><span class="stat-card-label">Approved</span></div>
            <div class="stat-card-value">${data.approved_claims}</div>
          </div>
          <div class="stat-card red">
            <div class="stat-card-header"><div class="stat-card-icon">❌</div><span class="stat-card-label">Rejected</span></div>
            <div class="stat-card-value">${data.rejected_claims}</div>
          </div>
          <div class="stat-card amber">
            <div class="stat-card-header"><div class="stat-card-icon">🚨</div><span class="stat-card-label">Escalated</span></div>
            <div class="stat-card-value">${data.escalated_claims}</div>
          </div>
        </div>
        <div class="charts-grid">
          <div class="glass-card">
            <div class="card-header"><h3>📊 Approval vs Rejection</h3></div>
            <div class="chart-container"><canvas id="approvalChart"></canvas></div>
          </div>
          <div class="glass-card">
            <div class="card-header"><h3>📈 Fraud Trend</h3></div>
            <div class="chart-container"><canvas id="trendChart2"></canvas></div>
          </div>
        </div>
      `;
            this.renderAnalyticsCharts(data);
        } catch (e) {
            document.getElementById('analytics-content').innerHTML = renderEmptyState('❌', 'Failed to load analytics');
        }
    },

    renderAnalyticsCharts(data) {
        Object.values(this.chartInstances).forEach(c => c?.destroy());
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Inter';

        const ctx1 = document.getElementById('approvalChart');
        if (ctx1) {
            this.chartInstances.approval = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: ['Approved', 'Rejected', 'Escalated', 'Pending'],
                    datasets: [{
                        data: [data.approved_claims, data.rejected_claims, data.escalated_claims, data.pending_claims],
                        backgroundColor: ['rgba(16,185,129,0.7)', 'rgba(244,63,94,0.7)', 'rgba(249,115,22,0.7)', 'rgba(245,158,11,0.7)'],
                        borderRadius: 8, borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
                },
            });
        }

        const ctx2 = document.getElementById('trendChart2');
        if (ctx2 && data.fraud_trend?.length) {
            this.chartInstances.trend = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: data.fraud_trend.map(d => d.date),
                    datasets: [{
                        label: 'Avg Fraud Probability', data: data.fraud_trend.map(d => d.avg_fraud_probability * 100),
                        borderColor: 'rgba(244,63,94,0.8)', backgroundColor: 'rgba(244,63,94,0.1)', fill: true, tension: 0.4, borderWidth: 2
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } },
                    scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '%' } }, x: { grid: { display: false }, ticks: { maxRotation: 45 } } }
                },
            });
        }
    },

    async renderAlerts() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('alerts', `
      <div class="top-bar"><div class="page-title"><h1>🔔 Fraud Alerts</h1><p>Suspicious pattern alerts</p></div></div>
      <div id="alerts-content">${renderLoading()}</div>
    `);
        try {
            const data = await API.getAlerts();
            document.getElementById('alerts-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card red"><div class="stat-card-header"><div class="stat-card-icon">🚨</div><span class="stat-card-label">Critical</span></div><div class="stat-card-value">${data.critical_alerts}</div></div>
          <div class="stat-card amber"><div class="stat-card-header"><div class="stat-card-icon">⚠️</div><span class="stat-card-label">High</span></div><div class="stat-card-value">${data.high_alerts}</div></div>
          <div class="stat-card blue"><div class="stat-card-header"><div class="stat-card-icon">ℹ️</div><span class="stat-card-label">Medium</span></div><div class="stat-card-value">${data.medium_alerts}</div></div>
        </div>
        <div class="glass-card">
          <div class="card-header"><h3>⚠️ Active Alerts (${data.total_alerts})</h3></div>
          ${data.alerts?.length ? data.alerts.map(a => `
            <div class="alert-item ${a.severity}">
              <span class="alert-icon">${a.severity === 'critical' ? '🚨' : a.severity === 'high' ? '⚠️' : 'ℹ️'}</span>
              <div class="alert-content">
                <div class="alert-title">${a.alert_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>
                <div class="alert-message">${a.message}</div>
              </div>
              <span class="badge badge-${a.severity}">${a.severity}</span>
            </div>
          `).join('') : renderEmptyState('✅', 'No active alerts')}
        </div>
      `;
        } catch (e) {
            document.getElementById('alerts-content').innerHTML = renderEmptyState('❌', 'Failed to load alerts');
        }
    },

    async renderAuditLogs() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('audit-logs', `
      <div class="top-bar"><div class="page-title"><h1>📜 Audit Logs</h1><p>System activity trail</p></div></div>
      <div class="glass-card"><div id="audit-table">${renderLoading()}</div></div>
    `);
        try {
            const data = await API.getAuditLogs({ page: 1, page_size: 50 });
            document.getElementById('audit-table').innerHTML = data.logs?.length ? `
        <div class="table-container"><table><thead><tr><th>Time</th><th>Action</th><th>User</th><th>Resource</th><th>Details</th></tr></thead><tbody>
          ${data.logs.map(l => `<tr>
            <td>${formatDateTime(l.created_at)}</td>
            <td><span class="badge badge-vehicle">${l.action}</span></td>
            <td>User #${l.user_id || '—'}</td>
            <td>${l.resource_type || '—'} #${l.resource_id || ''}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${JSON.stringify(l.details) || '—'}</td>
          </tr>`).join('')}
        </tbody></table></div>
      ` : renderEmptyState('📜', 'No audit logs found');
        } catch (e) {
            document.getElementById('audit-table').innerHTML = renderEmptyState('❌', 'Failed to load audit logs');
        }
    },

    async renderSettings() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('settings', `
      <div class="top-bar"><div class="page-title"><h1>⚙️ Settings</h1><p>Fraud detection configuration</p></div></div>
      <div class="glass-card" style="max-width:600px;">
        <h3 style="margin-bottom:var(--space-lg)">🎯 Threshold Configuration</h3>
        <div class="form-group">
          <label class="form-label">Low Risk Threshold (0-1)</label>
          <input type="number" class="form-input" id="threshold-low" min="0" max="1" step="0.05" value="0.3">
          <p style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Claims below this score are marked Low Risk</p>
        </div>
        <div class="form-group">
          <label class="form-label">High Risk Threshold (0-1)</label>
          <input type="number" class="form-input" id="threshold-high" min="0" max="1" step="0.05" value="0.7">
          <p style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">Claims above this score are marked High Risk</p>
        </div>
        <button class="btn btn-primary" onclick="Admin.saveThresholds()">Save Thresholds</button>
      </div>
    `);
        try {
            const t = await API.getThresholds();
            if (t) {
                document.getElementById('threshold-low').value = t.low_threshold;
                document.getElementById('threshold-high').value = t.high_threshold;
            }
        } catch (e) { }
    },

    async saveThresholds() {
        const low = parseFloat(document.getElementById('threshold-low').value);
        const high = parseFloat(document.getElementById('threshold-high').value);
        if (low >= high) { showToast('Low threshold must be less than high', 'warning'); return; }
        try {
            await API.updateThresholds(low, high);
            showToast('Thresholds updated!', 'success');
        } catch (e) { showToast('Failed to update', 'error'); }
    },
};
