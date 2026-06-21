import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    Users, Activity, Search, MousePointerClick, BarChart3,
    Sparkles, RefreshCw, Trash2, ShieldCheck, ShieldOff, UserCheck, UserX,
    LayoutDashboard, LineChart as LineIcon, Settings as SettingsIcon, Database,
} from 'lucide-react';
import {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, CartesianGrid, AreaChart, Area, RadarChart,
    Radar, PolarGrid, PolarAngleAxis,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import Particles from '../components/Particles';
import {
    adminAnalyticsOverview,
    adminAnalyticsSignups,
    adminAnalyticsActivity,
    adminAnalyticsTopProducts,
    adminAnalyticsSearches,
    adminAnalyticsRecommendations,
    adminListUsers,
    adminUpdateUser,
    adminReseed,
    adminReseedStatus,
} from '../services/api';
import './AdminPage.css';

const PIE_COLORS = ['#c9a84c', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#0ea5e9'];

const MENU = [
    { id: 'overview', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'analytics', icon: LineIcon, label: 'Analytics' },
    { id: 'users', icon: Users, label: 'Users' },
    { id: 'searches', icon: Search, label: 'Searches' },
    { id: 'recommendations', icon: BarChart3, label: 'Recommendations' },
    { id: 'ops', icon: SettingsIcon, label: 'Operations' },
];

function StatCard({ icon: Icon, label, value, hint }) {
    return (
        <motion.div className="stat-card" whileHover={{ y: -2 }}>
            <div className="stat-icon"><Icon size={20} /></div>
            <div>
                <div className="stat-value">{value ?? '—'}</div>
                <div className="stat-label">{label}</div>
                {hint && <div className="stat-hint">{hint}</div>}
            </div>
        </motion.div>
    );
}

export default function AdminPage() {
    const { user } = useAuth();
    const [tab, setTab] = useState('overview');
    const [overview, setOverview] = useState(null);
    const [signups, setSignups] = useState([]);
    const [activity, setActivity] = useState([]);
    const [topProducts, setTopProducts] = useState([]);
    const [searches, setSearches] = useState({ recent: [], top_queries: [] });
    const [recs, setRecs] = useState({ recent: [], by_source: [] });
    const [users, setUsers] = useState([]);
    const [reseed, setReseed] = useState(null);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState('');

    const loadAll = async () => {
        setLoading(true);
        setErr('');
        try {
            const [ov, su, ac, tp, sr, rl, us] = await Promise.all([
                adminAnalyticsOverview(),
                adminAnalyticsSignups(30),
                adminAnalyticsActivity(30),
                adminAnalyticsTopProducts(10),
                adminAnalyticsSearches(50),
                adminAnalyticsRecommendations(100),
                adminListUsers(),
            ]);
            setOverview(ov);
            setSignups(su);
            setActivity(ac);
            setTopProducts(tp);
            setSearches(sr);
            setRecs(rl);
            setUsers(us);
        } catch (e) {
            setErr(e?.response?.data?.error || e.message || 'Failed to load analytics');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadAll(); }, []);

    const refreshReseed = async () => {
        try { setReseed(await adminReseedStatus()); } catch { /* ignore */ }
    };

    const startReseed = async () => {
        await adminReseed();
        await refreshReseed();
    };

    const toggleRole = async (u) => {
        const next = u.role === 'admin' ? 'user' : 'admin';
        const updated = await adminUpdateUser(u.id, { role: next });
        setUsers((list) => list.map((x) => (x.id === updated.id ? updated : x)));
    };

    const toggleActive = async (u) => {
        const updated = await adminUpdateUser(u.id, { is_active: !u.is_active });
        setUsers((list) => list.map((x) => (x.id === updated.id ? updated : x)));
    };

    // Pivot daily activity into per-action lines
    const activityByDay = React.useMemo(() => {
        const byDay = {};
        for (const r of activity) {
            const d = (r.day || '').slice(0, 10);
            byDay[d] = byDay[d] || { day: d };
            byDay[d][r.action] = Number(r.total) || 0;
        }
        return Object.values(byDay).sort((a, b) => a.day.localeCompare(b.day));
    }, [activity]);

    return (
        <div className="dash admin-dash">
            <Particles count={18} />

            {/* ─── Sidebar (RecoML pattern) ─── */}
            <aside className="dash-side">
                <div className="who">
                    <div className="who-label">Signed in as</div>
                    <div className="who-name">
                        <ShieldCheck size={16} color="#e8c76a" />
                        {user?.username || 'admin'}
                    </div>
                    <span className="pill gold">Administrator</span>
                </div>

                <div className="dash-side-label">Navigation</div>
                {MENU.map((m) => {
                    const Icon = m.icon;
                    return (
                        <button
                            key={m.id}
                            className={`dash-item ${tab === m.id ? 'active' : ''}`}
                            onClick={() => setTab(m.id)}
                        >
                            <Icon size={16} />
                            <span>{m.label}</span>
                            {m.id === 'users' && users.length > 0 && (
                                <span className="badge-mini">{users.length}</span>
                            )}
                        </button>
                    );
                })}

                {/* Engine status panel */}
                <div className="dash-status">
                    <div className="dash-status-title"><Database size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} /> Engine Status</div>
                    {overview ? `✅ ${(overview.users_total ?? 0).toLocaleString()} users registered` : '⚪ Loading…'}
                    <br />{overview ? `✅ ${(overview.searches_24h ?? 0)} searches (24h)` : ''}
                    <br />{reseed?.running ? '⏳ Re-seed running' : '✅ Embeddings ready'}
                </div>
            </aside>

            {/* ─── Main ─── */}
            <div className="dash-main">
                <header className="admin-header">
                    <div>
                        <h1 className="admin-title"><Sparkles size={22} /> Admin Dashboard</h1>
                        <p className="admin-sub">Multi-modal Recommendation Engine · Control Panel</p>
                    </div>
                    <button className="admin-btn" onClick={loadAll} disabled={loading}>
                        <RefreshCw size={16} style={{ marginRight: 6 }} />
                        {loading ? 'Loading…' : 'Refresh'}
                    </button>
                </header>

                {err && <div className="alert-box danger">⚠ {err}</div>}

                {tab === 'overview' && overview && (
                    <>
                        <section className="admin-grid">
                            <StatCard icon={Users} label="Total users" value={overview.users_total} />
                            <StatCard icon={UserCheck} label="Signups (7d)" value={overview.signups_7d} />
                            <StatCard icon={Activity} label="Logins (24h)" value={overview.logins_24h} />
                            <StatCard icon={MousePointerClick} label="Product views (24h)" value={overview.product_views_24h} />
                            <StatCard icon={Search} label="Searches (24h)" value={overview.searches_24h} />
                            <StatCard icon={BarChart3} label="Recommendations (24h)" value={overview.recommendations_24h} />
                            <StatCard icon={MousePointerClick} label="Rec clicks (24h)" value={overview.rec_clicks_24h} />
                            <StatCard icon={Activity} label="CTR (24h)" value={`${overview.ctr_24h ?? 0}%`} hint="clicks / recs" />
                        </section>

                        {/* Quick actions strip (RecoML-inspired) */}
                        <div className="chart-card" style={{ marginTop: 16 }}>
                            <h3>⚡ Quick Actions</h3>
                            <div className="quick-actions">
                                {[
                                    { icon: '📊', label: 'View Analytics', target: 'analytics' },
                                    { icon: '👥', label: 'Manage Users', target: 'users' },
                                    { icon: '🔍', label: 'Search Logs', target: 'searches' },
                                    { icon: '✨', label: 'Reco Logs', target: 'recommendations' },
                                    { icon: '⚙️', label: 'Re-seed Engine', target: 'ops' },
                                ].map((a) => (
                                    <button key={a.target} className="admin-btn ghost" onClick={() => setTab(a.target)}>
                                        <span style={{ marginRight: 6 }}>{a.icon}</span>{a.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </>
                )}

                {tab === 'analytics' && (
                    <section className="admin-charts">
                        <div className="chart-card">
                            <h3>Daily signups (30d)</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <LineChart data={signups}>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis dataKey="day" stroke="#888" fontSize={11} />
                                    <YAxis stroke="#888" fontSize={11} allowDecimals={false} />
                                    <Tooltip contentStyle={{ background: '#1a1a23', border: '1px solid #333' }} />
                                    <Line type="monotone" dataKey="signups" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="chart-card">
                            <h3>User activity by action (30d)</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <LineChart data={activityByDay}>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis dataKey="day" stroke="#888" fontSize={11} />
                                    <YAxis stroke="#888" fontSize={11} allowDecimals={false} />
                                    <Tooltip contentStyle={{ background: '#1a1a23', border: '1px solid #333' }} />
                                    <Legend />
                                    <Line type="monotone" dataKey="view" stroke="#6366f1" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="like" stroke="#ec4899" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="search" stroke="#10b981" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="click_similar" stroke="#f59e0b" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="chart-card">
                            <h3>Top viewed products</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={topProducts}>
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis dataKey="product_id" stroke="#888" fontSize={11} />
                                    <YAxis stroke="#888" fontSize={11} allowDecimals={false} />
                                    <Tooltip contentStyle={{ background: '#1a1a23', border: '1px solid #333' }} />
                                    <Bar dataKey="views" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="chart-card">
                            <h3>Recommendations by source</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <PieChart>
                                    <Pie
                                        data={recs.by_source}
                                        dataKey="count"
                                        nameKey="source"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={80}
                                        label
                                    >
                                        {(recs.by_source || []).map((_, i) => (
                                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: '#1a1a23', border: '1px solid #333' }} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </section>
                )}

                {tab === 'users' && (
                    <section className="admin-table-wrap">
                        <table className="admin-table">
                            <thead>
                                <tr>
                                    <th>Username</th><th>Email</th><th>Role</th>
                                    <th>Status</th><th>Last login</th><th>Joined</th><th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((u) => (
                                    <tr key={u.id}>
                                        <td>{u.username}</td>
                                        <td>{u.email || '—'}</td>
                                        <td><span className={`badge ${u.role}`}>{u.role}</span></td>
                                        <td>
                                            <span className={`badge ${u.is_active ? 'ok' : 'off'}`}>
                                                {u.is_active ? 'active' : 'disabled'}
                                            </span>
                                        </td>
                                        <td>{u.last_login_at ? new Date(u.last_login_at).toLocaleString() : '—'}</td>
                                        <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                                        <td>
                                            <button className="row-btn" onClick={() => toggleRole(u)} title="Toggle admin role">
                                                {u.role === 'admin' ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                                            </button>
                                            <button className="row-btn" onClick={() => toggleActive(u)} title="Toggle active">
                                                {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {!users.length && <tr><td colSpan={7} style={{ textAlign: 'center', padding: 24 }}>No users</td></tr>}
                            </tbody>
                        </table>
                    </section>
                )}

                {tab === 'searches' && (
                    <section className="admin-charts">
                        <div className="chart-card">
                            <h3>Top search queries</h3>
                            <ResponsiveContainer width="100%" height={240}>
                                <BarChart data={searches.top_queries} layout="vertical">
                                    <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                                    <XAxis type="number" stroke="#888" fontSize={11} allowDecimals={false} />
                                    <YAxis type="category" dataKey="query" stroke="#888" fontSize={11} width={120} />
                                    <Tooltip contentStyle={{ background: '#1a1a23', border: '1px solid #333' }} />
                                    <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="admin-table-wrap" style={{ gridColumn: '1/-1' }}>
                            <table className="admin-table">
                                <thead><tr><th>Query</th><th>Results</th><th>Session</th><th>Time</th></tr></thead>
                                <tbody>
                                    {searches.recent.map((s, i) => (
                                        <tr key={i}>
                                            <td>{s.query}</td>
                                            <td>{s.result_count}</td>
                                            <td className="mono">{(s.session_id || '').slice(0, 8)}</td>
                                            <td>{new Date(s.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                    {!searches.recent.length && <tr><td colSpan={4} style={{ textAlign: 'center', padding: 24 }}>No searches yet</td></tr>}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {tab === 'recommendations' && (
                    <section className="admin-table-wrap">
                        <table className="admin-table">
                            <thead><tr><th>Source</th><th>Query</th><th>Results</th><th>Session</th><th>Time</th></tr></thead>
                            <tbody>
                                {recs.recent.map((r, i) => (
                                    <tr key={i}>
                                        <td><span className="badge">{r.source}</span></td>
                                        <td>{r.query || '—'}</td>
                                        <td>{r.result_count}</td>
                                        <td className="mono">{(r.session_id || '').slice(0, 8)}</td>
                                        <td>{new Date(r.created_at).toLocaleString()}</td>
                                    </tr>
                                ))}
                                {!recs.recent.length && <tr><td colSpan={5} style={{ textAlign: 'center', padding: 24 }}>No recommendations logged</td></tr>}
                            </tbody>
                        </table>
                    </section>
                )}

                {tab === 'ops' && (
                    <section className="admin-ops">
                        <div className="chart-card">
                            <h3>Re-seed embeddings</h3>
                            <p className="admin-sub">Run the embedding seeder script in the background.</p>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="admin-btn" onClick={startReseed}>Start re-seed</button>
                                <button className="admin-btn ghost" onClick={refreshReseed}>Refresh status</button>
                            </div>
                            {reseed && (
                                <pre className="admin-log">{JSON.stringify(reseed, null, 2)}</pre>
                            )}
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
}
