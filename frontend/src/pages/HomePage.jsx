import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, Upload, ArrowRight, Brain, Layers, Zap, Shield, Star, TrendingUp } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import { getPersonalizedRecommendations } from '../services/api';
import './HomePage.css';

export default function HomePage() {
    const [query, setQuery] = useState('');
    const [personalized, setPersonalized] = useState([]);
    const [personalizedLoading, setPersonalizedLoading] = useState(true);
    const [isPersonalized, setIsPersonalized] = useState(false);
    const navigate = useNavigate();

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
                </div>
            </section>

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
