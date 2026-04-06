import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, Upload, ArrowRight, Brain, Layers, Zap } from 'lucide-react';
import './HomePage.css';

export default function HomePage() {
    const [query, setQuery] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/catalog?search=${encodeURIComponent(query.trim())}`);
        }
    };

    const features = [
        {
            icon: <Brain size={28} />,
            title: 'Multi-Modal AI',
            desc: 'Fuses text descriptions, pricing signals, and brand context for deep product understanding.',
        },
        {
            icon: <Layers size={28} />,
            title: 'Hybrid Similarity',
            desc: 'TF-IDF + cosine similarity across 94K products with weighted feature fusion.',
        },
        {
            icon: <Zap size={28} />,
            title: 'Instant Results',
            desc: 'Real-time single queries or batch CSV uploads – recommendations in milliseconds.',
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
                        <Sparkles size={14} /> Powered by Multi-Modal ML
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
                        Discover similar products across 94,000+ items using advanced NLP,
                        pricing analysis, and brand intelligence – all in real-time.
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

            {/* ─── Features ─── */}
            <section className="features container">
                <div className="features-grid">
                    {features.map((f, i) => (
                        <motion.div
                            className="feature-card"
                            key={i}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.15 }}
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
                        ['3', 'Feature Modalities'],
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
