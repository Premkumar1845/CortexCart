import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Tag, TrendingDown, Zap, Heart, MessageCircle, Star } from 'lucide-react';
import { trackActivity, getExplanation } from '../services/api';
import './ProductCard.css';

export default function ProductCard({ product, index = 0 }) {
    const navigate = useNavigate();
    const [liked, setLiked] = useState(false);
    const [explanation, setExplanation] = useState('');
    const [showExplanation, setShowExplanation] = useState(false);
    const [loadingExplanation, setLoadingExplanation] = useState(false);

    const handleLike = (e) => {
        e.stopPropagation();
        setLiked(!liked);
        trackActivity(product.id, liked ? 'view' : 'like');
    };

    const handleExplain = async (e) => {
        e.stopPropagation();
        if (explanation) {
            setShowExplanation(!showExplanation);
            return;
        }
        setLoadingExplanation(true);
        setShowExplanation(true);
        try {
            const text = await getExplanation(product, 'Product recommendation');
            setExplanation(text);
        } catch {
            setExplanation(
                product.similarity_score > 0.5
                    ? `Strong ${(product.similarity_score * 100).toFixed(0)}% match based on features and brand.`
                    : 'Recommended based on product similarity analysis.'
            );
        } finally {
            setLoadingExplanation(false);
        }
    };

    const handleFindSimilar = () => {
        trackActivity(product.id, 'click_similar');
        navigate(`/recommendations/${product.id}`);
    };

    return (
        <motion.div
            className="product-card"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.05 }}
            whileHover={{ y: -6, scale: 1.02 }}
            layout
        >
            <div className="product-card-image">
                <img
                    src={product.imageUrl}
                    alt={product.name}
                    loading="lazy"
                />
                {product.discount_pct > 0 && (
                    <span className="product-card-badge">
                        <TrendingDown size={12} />
                        {product.discount_pct}% OFF
                    </span>
                )}
                <div className="product-card-actions-overlay">
                    <button
                        className={`product-card-like ${liked ? 'liked' : ''}`}
                        onClick={handleLike}
                        title={liked ? 'Unlike' : 'Like'}
                    >
                        <Heart size={16} fill={liked ? 'currentColor' : 'none'} />
                    </button>
                    {product.similarity_score !== undefined && (
                        <button
                            className="product-card-why"
                            onClick={handleExplain}
                            title="Why this product?"
                        >
                            <MessageCircle size={16} />
                        </button>
                    )}
                </div>
            </div>

            <div className="product-card-body">
                <span className="product-card-brand">{product.brandName}</span>
                <h3 className="product-card-name">{product.name}</h3>

                <div className="product-card-prices">
                    <span className="product-card-final">${product.finalPrice?.toLocaleString()}</span>
                    {product.retailPrice > product.finalPrice && (
                        <span className="product-card-retail">${product.retailPrice?.toLocaleString()}</span>
                    )}
                </div>

                <div className="product-card-meta">
                    <span><Tag size={12} /> {product.department}</span>
                    {product.rating > 0 && (
                        <span className="product-card-rating">
                            <Star size={12} /> {product.rating}
                        </span>
                    )}
                    {product.similarity_score !== undefined && (
                        <span className="product-card-score">
                            <Zap size={12} /> {(product.similarity_score * 100).toFixed(1)}% match
                        </span>
                    )}
                    {product.hybrid_score !== undefined && (
                        <span className="product-card-hybrid">
                            Score: {(product.hybrid_score * 100).toFixed(0)}
                        </span>
                    )}
                </div>

                <AnimatePresence>
                    {showExplanation && (
                        <motion.div
                            className="product-card-explanation"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                        >
                            {loadingExplanation ? (
                                <span className="explanation-loading">Analyzing...</span>
                            ) : (
                                <p>{explanation}</p>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>

                <button
                    className="product-card-btn"
                    onClick={handleFindSimilar}
                >
                    Find Similar
                </button>
            </div>
        </motion.div>
    );
}
