import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, Upload, ArrowRight, Brain, Layers, Zap, Shield, Star, TrendingUp, ShieldCheck, User as UserIcon, Cpu, Network, FlaskConical } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import Particles from '../components/Particles';
import { useAuth } from '../context/AuthContext';
import { getPersonalizedRecommendations } from '../services/api';
import './HomePage.css';

// Animated count-up hook (RecoML-inspired easing over fixed step count)
function useCountUp(target, { steps = 60, intervalMs = 18 } = {}) {
    const [val, setVal] = useState(0);
    const startedRef = useRef(false);
    useEffect(() => {
        if (startedRef.current) return;
        startedRef.current = true;
        let step = 0;
        const id = setInterval(() => {
            step += 1;
            setVal(Math.round((target * step) / steps));
            if (step >= steps) clearInterval(id);
        }, intervalMs);
        return () => clearInterval(id);
    }, [target, steps, intervalMs]);
    return val;
}

export default function HomePage() {
    const [query, setQuery] = useState('');
    const [personalized, setPersonalized] = useState([]);
    const [personalizedLoading, setPersonalizedLoading] = useState(true);
    const [isPersonalized, setIsPersonalized] = useState(false);
    const navigate = useNavigate();
    const { isAuthenticated, isAdmin } = useAuth();

    const products = useCountUp(94000);
    const brands = useCountUp(1400);
    const layers = useCountUp(5);
    const latency = useCountUp(100);

    useEffect(() => {
        async function loadPersonalized() {
            try {
                const data = await getPersonalizedRecommendations(8);
                setPersonalized(data.recommendations || []);
                setIsPersonalized(data.personalized || false);
            } catch {
                setPersonalized([]);
            } finally {
                setPersonalizedLoading(false);
            }
        }
        loadPersonalized();
    }, []);

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/catalog?search=${encodeURIComponent(query.trim())}`);
        }
    };

    const features = [
        {
            icon: <Brain size={28} />,
            title: 'Semantic Intelligence',
            desc: 'Vector embeddings understand product meaning, not just keywords. Find truly similar items across 94K+ products.',
        },
        {
            icon: <Layers size={28} />,
            title: 'Hybrid Ranking',
            desc: 'Multi-signal scoring fuses similarity, ratings, price proximity, and discounts for smarter recommendations.',
        },
        {
            icon: <Zap size={28} />,
            title: 'Real-time Results',
            desc: 'Single queries, batch CSV uploads, or AI chat – get intelligent recommendations in milliseconds.',
        },
        {
            icon: <Shield size={28} />,
            title: '"Why This?" Explainability',
            desc: 'Every recommendation comes with an AI-generated explanation of why it matches your needs.',
        },
        {
            icon: <Star size={28} />,
            title: 'Personalized For You',
            desc: 'Behavior tracking learns your preferences to deliver increasingly relevant product suggestions.',
        },
        {
            icon: <TrendingUp size={28} />,
            title: 'Smart Categories',
            desc: 'Best for you, budget alternatives, premium upgrades, and best value – organized decision layers.',
        },
    ];

    return (
        <div className="home">
            <Particles count={28} />
            {/* ─── Hero ─── */}
            <section className="hero">
                <motion.div
                    className="hero-glow"
                    animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.5, 0.3] }}
                    transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                />
                <div className="container hero-content">
                    <motion.span
                        className="hero-badge"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <Sparkles size={14} /> AI Decision Engine for Shopping
                    </motion.span>

                    <motion.h1
                        className="hero-title"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.35 }}
                    >
                        Intelligent Product<br />
                        <span className="hero-gradient">Recommendations</span>
                    </motion.h1>

                    <motion.p
                        className="hero-subtitle"
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                    >
                        Discover products through semantic understanding, hybrid ranking,
                        and AI-powered explanations – not just filters and sorting.
                    </motion.p>

                    <motion.form
                        className="hero-search"
                        onSubmit={handleSearch}
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.65 }}
                    >
                        <Search size={20} className="hero-search-icon" />
                        <input
                            type="text"
                            placeholder="Try &quot;Omega Speedmaster&quot; or &quot;diamond necklace&quot;…"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button type="submit">
                            Search <ArrowRight size={16} />
                        </button>
                    </motion.form>

                    <motion.div
                        className="hero-actions"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.8 }}
                    >
                        <button className="hero-cta-secondary" onClick={() => navigate('/catalog')}>
                            Explore Catalog
                        </button>
                        <button className="hero-cta-secondary" onClick={() => navigate('/batch')}>
                            <Upload size={16} /> Batch Upload
                        </button>
                    </motion.div>

                    {/* ─── Animated counter row (RecoML-inspired) ─── */}
                    <motion.div
                        className="hero-counters"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.95 }}
                    >
                        <div className="hero-counter">
                            <div className="hero-counter-num">{products.toLocaleString()}+</div>
                            <div className="hero-counter-label">Products Indexed</div>
                        </div>
                        <div className="hero-counter-divider" />
                        <div className="hero-counter">
                            <div className="hero-counter-num">{brands.toLocaleString()}+</div>
                            <div className="hero-counter-label">Brands</div>
                        </div>
                        <div className="hero-counter-divider" />
                        <div className="hero-counter">
                            <div className="hero-counter-num">{layers}</div>
                            <div className="hero-counter-label">Reco Layers</div>
                        </div>
                        <div className="hero-counter-divider" />
                        <div className="hero-counter">
                            <div className="hero-counter-num">&lt;{latency}ms</div>
                            <div className="hero-counter-label">Avg Response</div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* ─── Role-selection (RecoML-inspired admin/user portals) ─── */}
            {!isAuthenticated && (
                <section className="roles container">
                    <div className="roles-head">
                        <span className="hero-badge"><Sparkles size={14} /> Get Started</span>
                        <h2>Choose Your Portal</h2>
                        <p>Admins train, monitor and operate the engine. Users discover and shop with AI-powered guidance.</p>
                    </div>
                    <div className="roles-grid">
                        <motion.div
                            className="role-card admin"
                            whileHover={{ y: -4 }}
                            onClick={() => navigate('/login')}
                        >
                            <div className="role-icon"><ShieldCheck size={28} /></div>
                            <h3>Administrator</h3>
                            <p>Manage users · Live analytics · Re-seed embeddings · Inspect search & recommendation logs</p>
                            <button className="role-btn primary">Admin Login →</button>
                        </motion.div>
                        <motion.div
                            className="role-card user"
                            whileHover={{ y: -4 }}
                            onClick={() => navigate('/signup')}
                        >
                            <div className="role-icon"><UserIcon size={28} /></div>
                            <h3>Shopper</h3>
                            <p>Personalized recommendations · Batch CSV scoring · AI explanations · Smart catalog browse</p>
                            <button className="role-btn secondary">Create Account →</button>
                        </motion.div>
                    </div>
                </section>
            )}

            {isAuthenticated && (
                <section className="roles container">
                    <div className="roles-head">
                        <span className="hero-badge"><Sparkles size={14} /> Welcome Back</span>
                        <h2>{isAdmin ? 'Jump into operations' : 'Continue exploring'}</h2>
                    </div>
                    <div className="roles-grid">
                        <motion.div className="role-card user" whileHover={{ y: -4 }} onClick={() => navigate(isAdmin ? '/admin' : '/dashboard')}>
                            <div className="role-icon">{isAdmin ? <ShieldCheck size={28} /> : <UserIcon size={28} />}</div>
                            <h3>{isAdmin ? 'Admin Dashboard' : 'My Dashboard'}</h3>
                            <p>{isAdmin ? 'Analytics, users, ops & engine status.' : 'Browse, recommendations, batch & history.'}</p>
                            <button className="role-btn primary">Open →</button>
                        </motion.div>
                        <motion.div className="role-card admin" whileHover={{ y: -4 }} onClick={() => navigate('/catalog')}>
                            <div className="role-icon"><Search size={28} /></div>
                            <h3>Explore Catalog</h3>
                            <p>Search 94K+ products with semantic + hybrid ranking.</p>
                            <button className="role-btn secondary">Browse →</button>
                        </motion.div>
                    </div>
                </section>
            )}

            {/* ─── Personalized / Featured Section ─── */}
            <section className="personalized container">
                <motion.div
                    className="personalized-header"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                >
                    <h2>{isPersonalized ? '🔥 Recommended For You' : '🔥 Featured Products'}</h2>
                    {isPersonalized && (
                        <span className="personalized-badge">Based on your browsing</span>
                    )}
                </motion.div>
                {personalizedLoading ? (
                    <Loader text="Loading recommendations…" />
                ) : personalized.length > 0 ? (
                    <div className="personalized-grid">
                        {personalized.map((p, i) => (
                            <ProductCard key={p.id} product={p} index={i} />
                        ))}
                    </div>
                ) : null}
            </section>

            {/* ─── Features ─── */}
            <section className="features container">
                <motion.h2
                    className="features-title"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                >
                    Not Just Search. <span className="hero-gradient">Intelligence.</span>
                </motion.h2>
                <div className="features-grid">
                    {features.map((f, i) => (
                        <motion.div
                            className="feature-card"
                            key={i}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            whileHover={{ y: -4 }}
                        >
                            <div className="feature-icon">{f.icon}</div>
                            <h3>{f.title}</h3>
                            <p>{f.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* ─── ML Pipeline highlight (PDF-aligned) ─── */}
            <section className="ml-pipeline container">
                <motion.div
                    className="ml-pipeline-card"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                >
                    <div className="ml-pipeline-text">
                        <span className="hero-badge">
                            <Cpu size={14} /> Inside the Engine
                        </span>
                        <h2>
                            A Stacking Ensemble of <span className="hero-gradient">Four Models</span>
                        </h2>
                        <p>
                            HashingVectorizer text features fused with brand encoding and
                            scaled pricing flow into a stack of Gradient Boosting, LightGBM
                            and NGBoost — meta-learned by a Calibrated LinearSVC. Inspect
                            the architecture, live metrics and run predictions in the browser.
                        </p>
                        <ul className="ml-pipeline-list">
                            <li><Network size={16} /> Multi-modal sparse fusion (text + brand + price)</li>
                            <li><Layers size={16} /> Stacking ensemble with calibrated meta-learner</li>
                            <li><TrendingUp size={16} /> Live accuracy / precision / recall / F1 charts</li>
                            <li><FlaskConical size={16} /> Interactive classifier playground</li>
                        </ul>
                        <button className="hero-cta-secondary" onClick={() => navigate('/insights')}>
                            Open ML Insights <ArrowRight size={16} />
                        </button>
                    </div>
                    <div className="ml-pipeline-visual">
                        <div className="ml-pipeline-block input"><Brain size={18} /><span>text · brand · price</span></div>
                        <div className="ml-pipeline-arrow" />
                        <div className="ml-pipeline-block base">
                            <div className="ml-pipeline-sub">GBC</div>
                            <div className="ml-pipeline-sub">LGBM</div>
                            <div className="ml-pipeline-sub">NGB</div>
                        </div>
                        <div className="ml-pipeline-arrow" />
                        <div className="ml-pipeline-block meta"><Zap size={18} /><span>Calibrated LinearSVC</span></div>
                    </div>
                </motion.div>
            </section>

            {/* ─── Stats ─── */}
            <section className="stats container">
                <div className="stats-grid">
                    {[
                        ['94K+', 'Products'],
                        ['1,400+', 'Brands'],
                        ['5', 'Recommendation Layers'],
                        ['<100ms', 'Avg Response'],
                    ].map(([val, label], i) => (
                        <motion.div
                            className="stat"
                            key={i}
                            initial={{ opacity: 0, scale: 0.8 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <span className="stat-value">{val}</span>
                            <span className="stat-label">{label}</span>
                        </motion.div>
                    ))}
                </div>
            </section>
        </div>
    );
}
