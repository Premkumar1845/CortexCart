import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Zap, Tag, DollarSign, Star, TrendingUp, Gem, BadgeDollarSign, Heart } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import { fetchProduct, getSmartRecommendations, trackActivity } from '../services/api';
import './RecommendationsPage.css';

const SECTION_CONFIG = [
    { key: 'best_for_you', title: 'Best For You', icon: <Star size={20} />, color: 'gold' },
    { key: 'similar_products', title: 'Similar Products', icon: <Zap size={20} />, color: 'purple' },
    { key: 'budget_picks', title: 'Budget Alternatives', icon: <BadgeDollarSign size={20} />, color: 'green' },
    { key: 'premium_picks', title: 'Premium Upgrades', icon: <Gem size={20} />, color: 'pink' },
    { key: 'best_value', title: 'Best Value Deals', icon: <TrendingUp size={20} />, color: 'cyan' },
];

export default function RecommendationsPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [sections, setSections] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function go() {
            setLoading(true);
            try {
                const [prod, smartData] = await Promise.all([
                    fetchProduct(id),
                    getSmartRecommendations({ product_id: parseInt(id, 10), top_n: 20 }),
                ]);
                setProduct(prod);
                setSections(smartData.sections || {});
                trackActivity(id, 'view');
            } catch (err) {
                console.error(err);
                // Fallback: try legacy endpoint
                try {
                    const prod = await fetchProduct(id);
                    setProduct(prod);
                } catch { }
            } finally {
                setLoading(false);
            }
        }
        go();
    }, [id]);

    if (loading) return <Loader text="Analyzing product intelligence…" />;

    return (
        <div className="recs container">
            <button className="recs-back" onClick={() => navigate(-1)}>
                <ArrowLeft size={18} /> Back
            </button>

            {product && (
                <motion.div
                    className="recs-source"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="recs-source-img">
                        <img src={product.imageUrl} alt={product.name} />
                    </div>
                    <div className="recs-source-info">
                        <span className="recs-source-brand">{product.brandName}</span>
                        <h1 className="recs-source-name">{product.name}</h1>
                        <p className="recs-source-desc">{product.description_short}</p>
                        <div className="recs-source-meta">
                            <span><DollarSign size={14} /> ${product.finalPrice?.toLocaleString()}</span>
                            <span><Tag size={14} /> {product.department}</span>
                            {product.discount_pct > 0 && (
                                <span className="recs-source-discount">
                                    {product.discount_pct}% OFF
                                </span>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* ─── Categorized Recommendation Sections ─── */}
            {SECTION_CONFIG.map(({ key, title, icon, color }) => {
                const items = sections[key] || [];
                if (items.length === 0) return null;

                return (
                    <motion.section
                        key={key}
                        className={`recs-section recs-section--${color}`}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        <div className="recs-section-header">
                            <span className={`recs-section-icon recs-section-icon--${color}`}>{icon}</span>
                            <h2>{title}</h2>
                            <span className="recs-section-count">{items.length}</span>
                        </div>
                        <div className="recs-grid">
                            {items.map((r, i) => (
                                <ProductCard key={`${key}-${r.id}-${i}`} product={r} index={i} />
                            ))}
                        </div>
                    </motion.section>
                );
            })}

            {Object.values(sections).every(s => !s || s.length === 0) && !loading && (
                <div className="recs-empty">
                    <p>No recommendations found for this product.</p>
                </div>
            )}
        </div>
    );
}
