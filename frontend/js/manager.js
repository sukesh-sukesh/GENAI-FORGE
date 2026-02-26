/**
 * InsureGuard AI - Manager Module
 * Fraud intelligence, high-risk claims, and network detection.
 */

const Manager = {
    async renderFraudIntelligence() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('fraud-intel', `
      <div class="top-bar">
        <div class="page-title">
          <h1>🕵️ Fraud Intelligence</h1>
          <p>Advanced fraud detection insights and network analysis</p>
        </div>
      </div>
      <div id="intel-content">${renderLoading()}</div>
    `);

        try {
            const data = await API.getFraudIntelligence();
            const entities = data.entities || {};
            const networks = data.networks || {};
            const alerts = data.alerts || {};

            document.getElementById('intel-content').innerHTML = `
        <div class="stats-grid">
          <div class="stat-card red">
            <div class="stat-card-header">
              <div class="stat-card-icon">🕸️</div>
              <span class="stat-card-label">Fraud Networks</span>
            </div>
            <div class="stat-card-value">${networks.total_clusters || 0}</div>
          </div>
          <div class="stat-card amber">
            <div class="stat-card-header">
              <div class="stat-card-icon">👤</div>
              <span class="stat-card-label">Suspicious Entities</span>
            </div>
            <div class="stat-card-value">${entities.total_suspicious_entities || 0}</div>
          </div>
          <div class="stat-card blue">
            <div class="stat-card-header">
              <div class="stat-card-icon">🔗</div>
              <span class="stat-card-label">Network Nodes</span>
            </div>
            <div class="stat-card-value">${networks.total_nodes || 0}</div>
          </div>
          <div class="stat-card green">
            <div class="stat-card-header">
              <div class="stat-card-icon">🔔</div>
              <span class="stat-card-label">Active Alerts</span>
            </div>
            <div class="stat-card-value">${alerts.total_alerts || 0}</div>
          </div>
        </div>

        <!-- Fraud Networks -->
        <div class="glass-card">
          <div class="card-header">
            <h3>🕸️ Detected Fraud Networks</h3>
          </div>
          ${networks.fraud_clusters?.length > 0 ? networks.fraud_clusters.map((cluster, i) => `
            <div class="alert-item ${cluster.risk_level === 'critical' ? 'critical' : 'high'}" style="margin-bottom: var(--space-md);">
              <span class="alert-icon">${cluster.risk_level === 'critical' ? '🚨' : '⚠️'}</span>
              <div class="alert-content">
                <div class="alert-title">Network Cluster #${i + 1} — ${cluster.size} connected entities</div>
                <div class="alert-message">
                  Risk Level: <span class="badge badge-${cluster.risk_level}">${cluster.risk_level}</span>
                  <br>Entities: ${cluster.nodes.slice(0, 5).join(', ')}${cluster.nodes.length > 5 ? '...' : ''}
                </div>
              </div>
            </div>
          `).join('') : renderEmptyState('✅', 'No fraud networks detected')}
        </div>

        <!-- Repeated Entities -->
        <div class="charts-grid">
          <div class="glass-card">
            <div class="card-header"><h3>🔧 Repeated Repair Shops</h3></div>
            ${entities.repeated_repair_shops?.length > 0 ? `
              <div class="table-container"><table><thead><tr><th>Shop</th><th>Claims</th><th>Risk</th></tr></thead><tbody>
                ${entities.repeated_repair_shops.map(s => `
                  <tr><td>${s.shop_name}</td><td>${s.claim_count}</td><td>${renderRiskBadge(s.risk)}</td></tr>
                `).join('')}
              </tbody></table></div>
            ` : renderEmptyState('✅', 'No suspicious patterns')}
          </div>
          <div class="glass-card">
            <div class="card-header"><h3>🏥 Repeated Hospitals</h3></div>
            ${entities.repeated_hospitals?.length > 0 ? `
              <div class="table-container"><table><thead><tr><th>Hospital</th><th>Claims</th><th>Risk</th></tr></thead><tbody>
                ${entities.repeated_hospitals.map(h => `
                  <tr><td>${h.hospital_name}</td><td>${h.claim_count}</td><td>${renderRiskBadge(h.risk)}</td></tr>
                `).join('')}
              </tbody></table></div>
            ` : renderEmptyState('✅', 'No suspicious patterns')}
          </div>
        </div>

        <!-- Repeated Phones -->
        ${entities.repeated_phones?.length > 0 ? `
          <div class="glass-card">
            <div class="card-header"><h3>📱 Repeated Phone Numbers</h3></div>
            <div class="table-container"><table><thead><tr><th>Phone</th><th>Accounts</th><th>Risk</th></tr></thead><tbody>
              ${entities.repeated_phones.map(p => `
                <tr><td>${p.phone}</td><td>${p.account_count}</td><td>${renderRiskBadge(p.risk)}</td></tr>
              `).join('')}
            </tbody></table></div>
          </div>
        ` : ''}
      `;
        } catch (error) {
            console.error('Fraud intelligence error:', error);
            document.getElementById('intel-content').innerHTML =
                renderEmptyState('❌', 'Failed to load fraud intelligence. Manager access required.');
        }
    },

    async renderHighRiskClaims() {
        const app = document.getElementById('app');
        app.innerHTML = renderPageLayout('high-risk', `
      <div class="top-bar">
        <div class="page-title">
          <h1>🚨 High Risk Claims</h1>
          <p>Claims flagged for elevated fraud probability</p>
        </div>
      </div>
      <div class="glass-card"><div id="high-risk-table">${renderLoading()}</div></div>
    `);

        try {
            const data = await API.getHighRiskClaims();
            const claims = data.claims || [];

            document.getElementById('high-risk-table').innerHTML = claims.length > 0 ? `
        <div class="card-header">
          <h3>🔴 ${data.total} High Risk Claims</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Claim #</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Fraud Score</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${claims.map(c => `
                <tr>
                  <td><strong>${c.claim_number}</strong></td>
                  <td>${renderCategoryBadge(c.insurance_category)}</td>
                  <td>${formatCurrency(c.claim_amount)}</td>
                  <td>
                    <strong style="color: var(--accent-rose);">
                      ${c.fraud_probability ? (c.fraud_probability * 100).toFixed(1) + '%' : '—'}
                    </strong>
                  </td>
                  <td>${renderStatusBadge(c.status)}</td>
                  <td>${formatDate(c.created_at)}</td>
                  <td>
                    <button class="btn btn-ghost btn-sm" onclick="Claims.showDetail(${c.id})">
                      Investigate
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      ` : renderEmptyState('✅', 'No high-risk claims at this time');
        } catch (error) {
            document.getElementById('high-risk-table').innerHTML =
                renderEmptyState('❌', 'Failed to load high-risk claims');
        }
    },
};
