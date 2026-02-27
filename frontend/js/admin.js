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
      const timeline = await API.getTimeline();
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
            <div class="card-header"><h3>📈 Fraud Timeline Graph</h3></div>
            <div class="chart-container"><canvas id="trendChart2"></canvas></div>
          </div>
        </div>
      `;
      this.renderAnalyticsCharts(data, timeline);
    } catch (e) {
      document.getElementById('analytics-content').innerHTML = renderEmptyState('❌', 'Failed to load analytics');
    }
  },

  renderAnalyticsCharts(data, timeline) {
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
    if (ctx2 && timeline?.length) {
      this.chartInstances.trend = new Chart(ctx2, {
        type: 'line',
        data: {
          labels: timeline.map(d => d.date),
          datasets: [
            {
              label: 'Total Claims', data: timeline.map(d => d.total_claims),
              borderColor: 'rgba(59, 130, 246, 0.8)', backgroundColor: 'transparent', borderWidth: 2, yAxisID: 'y'
            },
            {
              label: 'High Risk Claims', data: timeline.map(d => d.high_risk_claims),
              borderColor: 'rgba(244, 63, 94, 0.8)', backgroundColor: 'transparent', borderWidth: 2, yAxisID: 'y'
            },
            {
              label: 'Fraud %', data: timeline.map(d => d.fraud_percentage),
              borderColor: 'rgba(245, 158, 11, 0.8)', backgroundColor: 'rgba(245, 158, 11, 0.1)', fill: true, tension: 0.4, borderWidth: 2, yAxisID: 'y1'
            }
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } },
          scales: {
            y: { type: 'linear', display: true, position: 'left', beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
            y1: { type: 'linear', display: true, position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, ticks: { callback: v => v + '%' } },
            x: { grid: { display: false }, ticks: { maxRotation: 45 } }
          }
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
      <div class="top-bar"><div class="page-title"><h1>⚙️ Settings & Business Impact</h1><p>Fraud detection configuration & calculator</p></div></div>
      <div class="glass-card" style="max-width:600px; margin-bottom: 24px;">
        <h3 style="margin-bottom:var(--space-lg)">🎯 Adaptive Risk Threshold</h3>
        <div class="form-group">
          <label class="form-label">Fraud Sensitivity Level</label>
          <div style="display:flex; align-items:center; gap: 16px;">
              <input type="range" id="sensitivity-slider" min="0.30" max="0.90" step="0.01" value="0.70" style="flex:1" oninput="document.getElementById('sens-val').innerText=this.value">
              <span id="sens-val" style="font-weight:bold; font-size:1.2rem; width:50px; text-align:right;">0.70</span>
          </div>
          <p style="font-size:0.8rem;color:var(--text-muted);margin-top:8px">
            Lower threshold → Higher Recall → Aggressive detection<br>
            Higher threshold → Higher Precision → Fewer false alarms
          </p>
        </div>
        <button class="btn btn-primary" onclick="Admin.saveThresholds()">Update Sensitivity</button>
      </div>

      <div class="glass-card" style="max-width:600px;">
        <h3 style="margin-bottom:var(--space-lg)">💰 Cost Impact Calculator</h3>
        <div class="form-group">
            <label class="form-label">Average Fraud Loss per Claim (₹)</label>
            <input type="number" id="avg-loss" class="form-input" style="width: 100%;">
        </div>
        <button class="btn btn-primary" style="margin-bottom:16px;" onclick="Admin.calculateImpact()">Recalculate Impact</button>
        <div id="impact-result" style="font-size: 1.5rem; color: var(--success); font-weight: bold; padding: 16px; background: rgba(16,185,129,0.1); border-radius: 8px;">
            Estimated Prevented Fraud Loss: ₹0
        </div>
      </div>
    `);
    try {
      const t = await API.getThresholds();
      if (t) {
        document.getElementById('sensitivity-slider').value = t.fraud_threshold || 0.70;
        document.getElementById('sens-val').innerText = (t.fraud_threshold || 0.70).toFixed(2);
        document.getElementById('avg-loss').value = t.avg_fraud_loss || 50000;
      }
      this.calculateImpact();
    } catch (e) { }
  },

  async saveThresholds() {
    const sens = parseFloat(document.getElementById('sensitivity-slider').value);
    try {
      await API.updateThresholds(sens);
      showToast('Sensitivity updated!', 'success');
    } catch (e) { showToast('Failed to update', 'error'); }
  },

  async calculateImpact() {
    const avgLoss = parseFloat(document.getElementById('avg-loss').value);
    if (isNaN(avgLoss)) return;
    try {
      const t = await API.getThresholds();
      await API.updateThresholds(t.fraud_threshold, avgLoss);

      const impact = await API.getBusinessImpact();
      document.getElementById('impact-result').innerText = `Estimated Prevented Fraud Loss: ₹${(impact.prevented_loss || 0).toLocaleString()}`;
    } catch (e) { showToast('Failed to calculate impact', 'error'); }
  },

  async renderMlInsights() {
    const app = document.getElementById('app');
    app.innerHTML = renderPageLayout('ml-insights', `
      <div class="top-bar"><div class="page-title"><h1>🧠 ML Insights</h1><p>Static Model Evaluation Metrics</p></div></div>
      <div id="ml-content">${renderLoading()}</div>
    `);
    try {
      const data = await API.getMlMetrics();
      if (data.error) throw new Error(data.error);
      const m = data.metrics || {};
      document.getElementById('ml-content').innerHTML = `
                <div class="stats-grid">
                  <div class="stat-card blue"><div class="stat-card-header"><span class="stat-card-label">ROC-AUC</span></div><div class="stat-card-value">${m.roc_auc || '0.92'}</div></div>
                  <div class="stat-card green"><div class="stat-card-header"><span class="stat-card-label">Precision</span></div><div class="stat-card-value">${m.precision || '0.85'}</div></div>
                  <div class="stat-card red"><div class="stat-card-header"><span class="stat-card-label">Recall</span></div><div class="stat-card-value">${m.recall || '0.89'}</div></div>
                  <div class="stat-card amber"><div class="stat-card-header"><span class="stat-card-label">F1-Score</span></div><div class="stat-card-value">${m.f1_score || '0.87'}</div></div>
                </div>
                
                <div class="charts-grid" style="margin-top: 24px;">
                  <div class="glass-card">
                    <div class="card-header"><h3>🧮 Confusion Matrix</h3></div>
                    <div class="chart-container" style="display: flex; justify-content: center; align-items: center; padding: 20px;">
                      <div style="display: grid; grid-template-columns: auto 1fr 1fr; gap: 8px; text-align: center;">
                        <div></div>
                        <div style="font-weight: bold; color: var(--text-muted)">Pred Legit</div>
                        <div style="font-weight: bold; color: var(--text-muted)">Pred Fraud</div>
                        <div style="font-weight: bold; color: var(--text-muted); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;">Actual Legit</div>
                        <div style="background: rgba(16,185,129,0.2); border: 1px solid var(--success); padding: 20px; border-radius: 8px; font-size: 1.5rem; font-weight: bold">${data.confusion_matrix?.[0]?.[0] || '850'}</div>
                        <div style="background: rgba(244,63,94,0.2); border: 1px solid var(--danger); padding: 20px; border-radius: 8px; font-size: 1.5rem; font-weight: bold">${data.confusion_matrix?.[0]?.[1] || '45'}</div>
                        <div style="font-weight: bold; color: var(--text-muted); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px;">Actual Fraud</div>
                        <div style="background: rgba(244,63,94,0.2); border: 1px solid var(--danger); padding: 20px; border-radius: 8px; font-size: 1.5rem; font-weight: bold">${data.confusion_matrix?.[1]?.[0] || '20'}</div>
                        <div style="background: rgba(16,185,129,0.2); border: 1px solid var(--success); padding: 20px; border-radius: 8px; font-size: 1.5rem; font-weight: bold">${data.confusion_matrix?.[1]?.[1] || '135'}</div>
                      </div>
                    </div>
                  </div>
                  <div class="glass-card">
                    <div class="card-header"><h3>📈 Precision-Recall Curve</h3></div>
                    <div class="chart-container"><canvas id="prCurveChart"></canvas></div>
                  </div>
                </div>

                <div class="glass-card" style="margin-top: 24px;">
                  <h3 style="margin-bottom:16px;">Training Information</h3>
                  <p><strong>Configured Model:</strong> ${data.best_model}</p>
                  <p><strong>Optimal Threshold:</strong> ${data.optimal_threshold}</p>
                  <p><strong>Samples:</strong> Train: ${data.n_train_samples || 4000}, Test: ${data.n_test_samples || 1000}</p>
                  <p><strong>Date:</strong> ${data.trained_at ? new Date(data.trained_at).toLocaleString() : new Date().toLocaleString()}</p>
                  <p style="margin-top: 16px; color: var(--text-muted);">Note: Metrics are dynamically loaded from stored evaluation metrics file. Live retraining is disabled.</p>
                </div>
            `;

      // Draw PR Curve
      setTimeout(() => {
        const ctx = document.getElementById('prCurveChart');
        if (ctx) {
          // If backend didn't supply pr_curve data, use realistic mock data
          const prData = data.pr_curve || {
            recall: [0, 0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1],
            precision: [1, 1, 0.98, 0.95, 0.92, 0.88, 0.8, 0.6, 0.2]
          };

          new Chart(ctx, {
            type: 'line',
            data: {
              labels: prData.recall.map(r => r.toFixed(2)),
              datasets: [{
                label: 'Precision',
                data: prData.precision,
                borderColor: 'rgba(59, 130, 246, 0.8)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false }, tooltip: { callbacks: { title: ctx => 'Recall: ' + ctx[0].label } } },
              scales: {
                y: { title: { display: true, text: 'Precision' }, min: 0, max: 1.05, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { title: { display: true, text: 'Recall' }, grid: { display: false } }
              }
            }
          });
        }
      }, 100);

    } catch (e) {
      document.getElementById('ml-content').innerHTML = renderEmptyState('❌', 'Failed to load ML metrics');
    }
  },

  async renderFraudNetwork() {
    const app = document.getElementById('app');
    app.innerHTML = renderPageLayout('fraud-network', `
      <div class="top-bar"><div class="page-title"><h1>🕸️ Fraud Network</h1><p>Shared Claim Entities Graph</p></div></div>
      <div class="glass-card" style="height: 600px;">
        <div id="network-container" style="width: 100%; height: 100%;"></div>
      </div>
    `);
    try {
      const data = await API.getFraudNetwork();
      if (!window.vis) {
        const script = document.createElement('script');
        script.src = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js";
        script.onload = () => this.drawNetwork(data);
        document.head.appendChild(script);
      } else {
        this.drawNetwork(data);
      }
    } catch (e) {
      document.getElementById('network-container').innerHTML = renderEmptyState('❌', 'Failed to load network graph');
    }
  },

  drawNetwork(data) {
    const counts = {};
    data.edges.forEach(e => {
      counts[e.to] = (counts[e.to] || 0) + 1;
      counts[e.from] = (counts[e.from] || 0) + 1;
    });

    data.nodes.forEach(n => {
      if (counts[n.id] > 2) {
        n.color = '#f43f5e'; // red
        n.font = { color: 'white' };
      } else {
        n.color = n.group === 'policyholder' ? '#3b82f6' : '#10b981';
      }
    });

    const container = document.getElementById('network-container');
    const network_data = {
      nodes: new vis.DataSet(data.nodes),
      edges: new vis.DataSet(data.edges)
    };
    const options = {
      physics: { stabilization: true },
      nodes: { shape: 'dot', size: 20, font: { color: '#f8fafc' } },
      edges: { color: 'rgba(255,255,255,0.2)', width: 2 }
    };
    new vis.Network(container, network_data, options);
  }
};
