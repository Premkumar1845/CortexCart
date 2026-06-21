import axios from 'axios';

const API = axios.create({ baseURL: '/api' });

// ── Auth token injection ─────────────────────────────────────────────
export function setAuthToken(token) {
    if (token) {
        API.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
        delete API.defaults.headers.common.Authorization;
    }
}

// On boot, restore token from localStorage so requests are authenticated
const _bootToken = typeof window !== 'undefined' ? localStorage.getItem('cortexcart_token') : null;
if (_bootToken) setAuthToken(_bootToken);

// ── Session Management ───────────────────────────────────────────────
const SESSION_KEY = 'cortexcart_session';

export function getSessionId() {
    let sid = localStorage.getItem(SESSION_KEY);
    if (!sid) {
        sid = crypto.randomUUID?.() || Math.random().toString(36).slice(2);
        localStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
}

// ── Products ─────────────────────────────────────────────────────────
export async function fetchProducts(page = 1, perPage = 20, search = '') {
    const params = { page, per_page: perPage };
    if (search) params.search = search;
    const { data } = await API.get('/products', { params });
    return data;
}

export async function fetchProduct(id) {
    const { data } = await API.get(`/products/${id}`);
    return data;
}

// ── Recommendations ──────────────────────────────────────────────────
export async function getRealtimeRecommendations({ product_id, query, brand, top_n = 10 }) {
    const { data } = await API.post('/recommend/realtime', {
        product_id,
        query,
        brand,
        top_n,
    });
    return data.recommendations;
}

export async function getSmartRecommendations({ product_id, query, brand, top_n = 20 }) {
    const { data } = await API.post('/recommend/smart', {
        product_id,
        query,
        brand,
        top_n,
        session_id: getSessionId(),
    });
    return data;
}

export async function getPersonalizedRecommendations(top_n = 10) {
    const { data } = await API.post('/recommend/personalized', {
        session_id: getSessionId(),
        top_n,
    });
    return data;
}

// ── AI Explanation ───────────────────────────────────────────────────
export async function getExplanation(product, context = '', userQuery = '') {
    const { data } = await API.post('/recommend/explain', {
        product,
        context,
        user_query: userQuery,
    });
    return data.explanation;
}

// ── Behavior Tracking ────────────────────────────────────────────────
export async function trackActivity(productId, action, metadata = {}) {
    try {
        await API.post('/track', {
            session_id: getSessionId(),
            product_id: String(productId),
            action,
            metadata,
        });
    } catch {
        // Silent fail – tracking should not block UX
    }
}

// ── Batch ────────────────────────────────────────────────────────────
export async function getBatchRecommendations(file, topN = 5) {
    const form = new FormData();
    form.append('file', file);
    form.append('top_n', topN);
    form.append('format', 'json');
    const { data } = await API.post('/recommend/batch', form);
    return data;
}

export async function downloadBatchCSV(file, topN = 5) {
    const form = new FormData();
    form.append('file', file);
    form.append('top_n', topN);
    form.append('format', 'csv');
    const response = await API.post('/recommend/batch', form, {
        responseType: 'blob',
    });
    return response.data;
}

// ── AI Chat ──────────────────────────────────────────────────────────
export async function getAIRecommendation(message) {
    try {
        const { data } = await API.post('/ai/recommend', { message });
        return data.reply;
    } catch (err) {
        const serverMsg = err?.response?.data?.error;
        throw new Error(serverMsg || err?.message || 'AI request failed');
    }
}

// ── Auth ─────────────────────────────────────────────────────────────
export async function apiSignup({ username, email, password, full_name }) {
    const { data } = await API.post('/auth/signup', { username, email, password, full_name });
    return data;
}

export async function apiLogin(username, password) {
    const { data } = await API.post('/auth/login', { username, password });
    return data;
}

export async function apiLogout() {
    const { data } = await API.post('/auth/logout');
    return data;
}

export async function apiMe() {
    const { data } = await API.get('/auth/me');
    return data;
}

// ── Recommendation click tracking ────────────────────────────────────
export async function trackRecommendationClick({ product_id, position, rec_log_id }) {
    try {
        await API.post('/recommend/click', {
            product_id: String(product_id),
            position,
            rec_log_id,
            session_id: getSessionId(),
        });
    } catch { /* silent */ }
}

// ── Admin: analytics ─────────────────────────────────────────────────
export async function adminAnalyticsOverview() {
    const { data } = await API.get('/admin/analytics/overview');
    return data;
}

export async function adminAnalyticsSignups(days = 30) {
    const { data } = await API.get('/admin/analytics/signups', { params: { days } });
    return data.data || [];
}

export async function adminAnalyticsActivity(days = 30) {
    const { data } = await API.get('/admin/analytics/activity', { params: { days } });
    return data.data || [];
}

export async function adminAnalyticsTopProducts(limit = 10) {
    const { data } = await API.get('/admin/analytics/top-products', { params: { limit } });
    return data.data || [];
}

export async function adminAnalyticsSearches(limit = 50) {
    const { data } = await API.get('/admin/analytics/searches', { params: { limit } });
    return data;
}

export async function adminAnalyticsRecommendations(limit = 100) {
    const { data } = await API.get('/admin/analytics/recommendations', { params: { limit } });
    return data;
}

// ── Admin: users + products ──────────────────────────────────────────
export async function adminListUsers() {
    const { data } = await API.get('/admin/users');
    return data.users || [];
}

export async function adminUpdateUser(userId, patch) {
    const { data } = await API.patch(`/admin/users/${userId}`, patch);
    return data.user;
}

export async function adminDeleteProduct(productId) {
    const { data } = await API.delete(`/admin/products/${productId}`);
    return data;
}

export async function adminUpdateProduct(productId, patch) {
    const { data } = await API.patch(`/admin/products/${productId}`, patch);
    return data;
}

export async function adminReseed() {
    const { data } = await API.post('/admin/reseed');
    return data;
}

export async function adminReseedStatus() {
    const { data } = await API.get('/admin/reseed/status');
    return data;
}

// ── ML Pipeline (PDF-aligned stacking ensemble) ──────────────────────
export async function getMLArchitecture() {
    const { data } = await API.get('/ml/architecture');
    return data;
}

export async function getMLMetrics() {
    const { data } = await API.get('/ml/metrics');
    return data;
}

export async function classifyProduct({ text, brand, price, discount_pct, top_k = 5 }) {
    const { data } = await API.post('/ml/classify', {
        text,
        brand,
        price,
        discount_pct,
        top_k,
    });
    return data;
}
