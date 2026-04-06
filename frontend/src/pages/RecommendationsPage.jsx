import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Zap, Tag, DollarSign } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import { fetchProduct, getRealtimeRecommendations } from '../services/api';
import './RecommendationsPage.css';

export default function RecommendationsPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [product, setProduct] = useState(null);
    const [recs, setRecs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function go() {
            setLoading(true);
            try {
                const [prod, recommendations] = await Promise.all([
                    fetchProduct(id),
                    getRealtimeRecommendations({ product_id: parseInt(id, 10), top_n: 12 }),
                ]);
                setProduct(prod);
                setRecs(recommendations);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        go();
    }, [id]);

    if (loading) return <Loader text="Finding similar products…" />;

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

            <motion.div
                className="recs-header"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
            >
                <Zap size={20} />
                <h2>Similar Products ({recs.length})</h2>
            </motion.div>

            <div className="recs-grid">
                {recs.map((r, i) => (
                    <ProductCard key={r.id} product={r} index={i} />
                ))}
            </div>
        </div>
    );
}
