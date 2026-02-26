/**
 * InsureGuard AI - Authentication Module
 * Handles login, registration, and session management.
 */

const Auth = {
    /**
     * Check if user is logged in.
     */
    isLoggedIn() {
        return !!localStorage.getItem(CONFIG.TOKEN_KEY);
    },

    /**
     * Get current user data.
     */
    getUser() {
        const data = localStorage.getItem(CONFIG.USER_KEY);
        return data ? JSON.parse(data) : null;
    },

    /**
     * Get user role.
     */
    getRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },

    /**
     * Store auth data after login.
     */
    setAuth(token, user) {
        localStorage.setItem(CONFIG.TOKEN_KEY, token);
        localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
    },

    /**
     * Clear auth data (logout).
     */
    logout() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_KEY);
        App.navigate('login');
    },

    /**
     * Render login/register page.
     */
    renderAuthPage() {
        const app = document.getElementById('app');
        app.innerHTML = `
      <div class="auth-page">
        <div class="auth-container">
          <div class="auth-card">
            <div class="auth-logo">
              <div class="logo-icon">🛡️</div>
              <h1>InsureGuard AI</h1>
              <p>Fraud Detection & Risk Intelligence</p>
            </div>

            <div class="auth-tabs">
              <button class="auth-tab active" id="tab-login" onclick="Auth.switchTab('login')">Sign In</button>
              <button class="auth-tab" id="tab-register" onclick="Auth.switchTab('register')">Sign Up</button>
            </div>

            <!-- Login Form -->
            <form id="login-form" onsubmit="Auth.handleLogin(event)">
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-input" id="login-email" placeholder="your@email.com" required>
              </div>
              <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" class="form-input" id="login-password" placeholder="••••••••" required>
              </div>
              <button type="submit" class="btn btn-primary btn-block btn-lg" id="login-btn">
                Sign In
              </button>
              <div class="mt-md text-center" style="font-size: 0.8rem; color: var(--text-muted);">
                <p>Demo Accounts:</p>
                <p>Admin: admin@insureguard.in / admin123</p>
                <p>Agent: agent@insureguard.in / agent123</p>
                <p>User: user@insureguard.in / user123</p>
              </div>
            </form>

            <!-- Register Form -->
            <form id="register-form" class="hidden" onsubmit="Auth.handleRegister(event)">
              <div class="form-group">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-input" id="reg-name" placeholder="John Doe" required minlength="2">
              </div>
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-input" id="reg-email" placeholder="your@email.com" required>
              </div>
              <div class="form-group">
                <label class="form-label">Phone (Optional)</label>
                <input type="tel" class="form-input" id="reg-phone" placeholder="9876543210" pattern="[6-9][0-9]{9}">
              </div>
              <div class="form-group">
                <label class="form-label">Password</label>
                <input type="password" class="form-input" id="reg-password" placeholder="••••••••" required minlength="6">
              </div>
              <div class="form-group">
                <label class="form-label">Account Type</label>
                <select class="form-select" id="reg-role">
                  <option value="user">Policyholder</option>
                  <option value="agent">Claims Agent</option>
                  <option value="manager">Manager</option>
                </select>
              </div>
              <button type="submit" class="btn btn-primary btn-block btn-lg" id="register-btn">
                Create Account
              </button>
            </form>
          </div>
        </div>
      </div>
    `;
    },

    /**
     * Switch between login and register tabs.
     */
    switchTab(tab) {
        document.getElementById('tab-login').classList.toggle('active', tab === 'login');
        document.getElementById('tab-register').classList.toggle('active', tab === 'register');
        document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
        document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
    },

    /**
     * Handle login form submission.
     */
    async handleLogin(e) {
        e.preventDefault();
        const btn = document.getElementById('login-btn');
        btn.disabled = true;
        btn.textContent = 'Signing in...';

        try {
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            const data = await API.login(email, password);
            if (data) {
                Auth.setAuth(data.access_token, data.user);
                showToast(`Welcome back, ${data.user.full_name}!`, 'success');
                App.navigate('dashboard');
            }
        } catch (error) {
            showToast(error.message || 'Login failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    },

    /**
     * Handle register form submission.
     */
    async handleRegister(e) {
        e.preventDefault();
        const btn = document.getElementById('register-btn');
        btn.disabled = true;
        btn.textContent = 'Creating account...';

        try {
            const userData = {
                full_name: document.getElementById('reg-name').value,
                email: document.getElementById('reg-email').value,
                phone: document.getElementById('reg-phone').value || undefined,
                password: document.getElementById('reg-password').value,
                role: document.getElementById('reg-role').value,
            };

            await API.register(userData);
            showToast('Account created successfully! Please sign in.', 'success');
            Auth.switchTab('login');
        } catch (error) {
            showToast(error.message || 'Registration failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Create Account';
        }
    },
};
