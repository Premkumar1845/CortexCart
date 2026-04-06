import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Tag, TrendingDown, Zap } from 'lucide-react';
import './ProductCard.css';

export default function ProductCard({ product, index = 0 }) {
    const navigate = useNavigate();

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
                    {product.similarity_score !== undefined && (
                        <span className="product-card-score">
                            <Zap size={12} /> {(product.similarity_score * 100).toFixed(1)}% match
                        </span>
                    )}
                </div>

                <button
                    className="product-card-btn"
                    onClick={() => navigate(`/recommendations/${product.id}`)}
                >
                    Find Similar
                </button>
            </div>
        </motion.div>
    );
}
