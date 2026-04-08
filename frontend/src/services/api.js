import axios from 'axios';

const API = axios.create({ baseURL: '/api' });

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
    const { data } = await API.post('/ai/recommend', { message });
    return data.reply;
}
