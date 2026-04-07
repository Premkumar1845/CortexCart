import axios from 'axios';

const API = axios.create({ baseURL: '/api' });

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

export async function getRealtimeRecommendations({ product_id, query, brand, top_n = 10 }) {
    const { data } = await API.post('/recommend/realtime', {
        product_id,
        query,
        brand,
        top_n,
    });
    return data.recommendations;
}

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

export async function getAIRecommendation(message) {
    const { data } = await API.post('/ai/recommend', { message });
    return data.reply;
}
