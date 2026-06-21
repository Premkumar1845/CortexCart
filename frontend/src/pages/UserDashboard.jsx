import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
    Search, Sparkles, Upload, History, User as UserIcon, ArrowRight,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Particles from '../components/Particles';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import {
    fetchProducts,
    getSmartRecommendations,
    getPersonalizedRecommendations,
    getSessionId,
} from '../services/api';
import './UserDashboard.css';

const MENU = [
    { id: 'browse', icon: Search, label: 'Browse Products' },
    { id: 'recommend', icon: Sparkles, label: 'Get Recommendations' },
    { id: 'upload', icon: Upload, label: 'Batch Upload' },
    { id: 'history', icon: History, label: 'My Recent' },
];

/**
 * User-facing dashboard mirroring the RecoML "User Portal" pattern:
 *   - Sidebar nav: Browse / Recommend / Upload / History
 *   - Each panel wires into existing CortexCart APIs
 *     (no fake data; reuses /products, /recommend/smart, /recommend/personalized).
 */
export default function UserDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [page, setPage] = useState('browse');

    // Browse state
    const [search, setSearch] = useState('');
    const [products, setProducts] = useState([]);
    const [loadingBrowse, setLoadingBrowse] = useState(false);

    // Recommendation form
    const [recQuery, setRecQuery] = useState('');
    const [recBrand, setRecBrand] = useState('');
    const [recResults, setRecResults] = useState([]);
    const [recLoading, setRecLoading] = useState(false);
    const [recError, setRecError] = useState('');

    // History (personalized = signal-driven; serves as "recent" view)
    const [history, setHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    // Fetch on entering each panel
    useEffect(() => {
        if (page === 'browse') {
            setLoadingBrowse(true);
            fetchProducts(1, 12, search)
                .then((d) => setProducts(d.products || []))
                .catch(() => setProducts([]))
                .finally(() => setLoadingBrowse(false));
        }
        if (page === 'history') {
            setHistoryLoading(true);
            getPersonalizedRecommendations(8)
                .then((d) => setHistory(d.recommendations || []))
                .catch(() => setHistory([]))
                .finally(() => setHistoryLoading(false));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page]);

    const runBrowseSearch = (e) => {
        e.preventDefault();
        setLoadingBrowse(true);
        fetchProducts(1, 12, search)
            .then((d) => setProducts(d.products || []))
            .catch(() => setProducts([]))
            .finally(() => setLoadingBrowse(false));
    };

    const runRecommend = async (e) => {
        e.preventDefault();
        setRecError('');
        setRecLoading(true);
        try {
            const data = await getSmartRecommendations({
                query: recQuery || undefined,
                brand: recBrand || undefined,
                top_n: 8,
            });
            const flat = (data?.recommendations || []).flatMap((g) => g.items || []);
            setRecResults(flat);
        } catch (err) {
            setRecError(err?.response?.data?.error || err.message || 'Failed');
            setRecResults([]);
        } finally {
            setRecLoading(false);
        }
    };

    return (
        <div className="dash user-dash">
            <Particles count={18} />

            <aside className="dash-side">
                <div className="who">
                    <div className="who-label">Signed in as</div>
                    <div className="who-name">
                        <UserIcon size={16} color="#a29bfe" />
                        {user?.username || 'guest'}
                    </div>
                    <span className="pill accent">Member</span>
                </div>

                <div className="dash-side-label">Navigation</div>
                {MENU.map((m) => {
                    const Icon = m.icon;
                    return (
                        <button
                            key={m.id}
                            className={`dash-item ${page === m.id ? 'active' : ''}`}
                            onClick={() => setPage(m.id)}
                        >
                            <Icon size={16} />
                            <span>{m.label}</span>
                        </button>
                    );
                })}

                <div className="dash-status">
                    <div className="dash-status-title">AI-Powered</div>
                    Hybrid TF-IDF + vector engine<br />
                    94K+ products indexed<br />
                    Session: <code>{(getSessionId() || '').slice(0, 8)}</code>
                </div>
            </aside>

            <div className="dash-main">
                {page === 'browse' && (
                    <div>
                        <header className="dash-page-head">
                            <h1>🔍 Browse Products</h1>
                            <p>Explore the CortexCart catalog with semantic search.</p>
                        </header>
                        <form className="ud-search" onSubmit={runBrowseSearch}>
                            <Search size={16} />
                            <input
                                type="text"
                                placeholder="Search by name, brand, or category…"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                            <button type="submit">Search</button>
                        </form>
                        {loadingBrowse ? (
                            <Loader text="Loading products…" />
                        ) : (
                            <div className="ud-grid">
                                {products.map((p, i) => (
                                    <ProductCard key={p.id} product={p} index={i} />
                                ))}
                                {!products.length && (
                                    <div className="alert-box gold">No products matched your query.</div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {page === 'recommend' && (
                    <div>
                        <header className="dash-page-head">
                            <h1>✨ Get Recommendations</h1>
                            <p>Describe a product or pick a brand — the engine ranks the best matches.</p>
                        </header>
                        <form className="ud-form chart-card" onSubmit={runRecommend}>
                            <div className="ud-field">
                                <label>Description</label>
                                <input
                                    placeholder="e.g. stainless steel automatic men's watch"
                                    value={recQuery}
                                    onChange={(e) => setRecQuery(e.target.value)}
                                />
                            </div>
                            <div className="ud-field">
                                <label>Brand (optional)</label>
                                <input
                                    placeholder="e.g. Omega"
                                    value={recBrand}
                                    onChange={(e) => setRecBrand(e.target.value)}
                                />
                            </div>
                            <button className="admin-btn" type="submit" disabled={recLoading}>
                                {recLoading ? 'Scoring…' : 'Get AI Recommendation'} <ArrowRight size={14} />
                            </button>
                            {recError && <div className="alert-box danger">{recError}</div>}
                        </form>

                        {recResults.length > 0 && (
                            <div className="ud-grid">
                                {recResults.slice(0, 12).map((p, i) => (
                                    <ProductCard key={p.id || i} product={p} index={i} />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {page === 'upload' && (
                    <div>
                        <header className="dash-page-head">
                            <h1>📤 Batch Upload</h1>
                            <p>Score a CSV of products via the existing batch endpoint.</p>
                        </header>
                        <div className="alert-box gold">
                            Batch scoring lives on its dedicated page with progress + CSV download.
                        </div>
                        <button className="admin-btn" onClick={() => navigate('/batch')}>
                            Open Batch Page <ArrowRight size={14} />
                        </button>
                    </div>
                )}

                {page === 'history' && (
                    <div>
                        <header className="dash-page-head">
                            <h1>📋 My Recent</h1>
                            <p>Personalized picks based on your tracked behaviour.</p>
                        </header>
                        {historyLoading ? (
                            <Loader text="Loading…" />
                        ) : history.length ? (
                            <div className="ud-grid">
                                {history.map((p, i) => (
                                    <ProductCard key={p.id || i} product={p} index={i} />
                                ))}
                            </div>
                        ) : (
                            <div className="alert-box gold">
                                No recent activity yet. Browse a few products to seed personalization.{' '}
                                <Link to="/catalog" style={{ color: 'var(--gold-light)', fontWeight: 700 }}>
                                    Start exploring →
                                </Link>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
