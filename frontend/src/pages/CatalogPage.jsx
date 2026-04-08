import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import { fetchProducts, trackActivity } from '../services/api';
import './CatalogPage.css';

export default function CatalogPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [meta, setMeta] = useState({ page: 1, total_pages: 1, total: 0 });
    const [search, setSearch] = useState(searchParams.get('search') || '');
    const [inputVal, setInputVal] = useState(searchParams.get('search') || '');

    const load = useCallback(async (page = 1, query = search) => {
        setLoading(true);
        try {
            const data = await fetchProducts(page, 20, query);
            setProducts(data.products);
            setMeta({ page: data.page, total_pages: data.total_pages, total: data.total });

            // Track product views for personalization
            if (data.products && data.products.length > 0) {
                data.products.slice(0, 5).forEach((p) => trackActivity(p.id, 'view'));
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [search]);

    useEffect(() => {
        // Track search queries for personalization
        if (search) {
            trackActivity(null, 'search', { query: search });
        }
        load(1, search);
    }, [search]);

    const handleSearch = (e) => {
        e.preventDefault();
        setSearch(inputVal);
        setSearchParams(inputVal ? { search: inputVal } : {});
    };

    return (
        <div className="catalog container">
            <div className="catalog-header">
                <div>
                    <h1 className="catalog-title">Explore Products</h1>
                    <p className="catalog-sub">{meta.total.toLocaleString()} products available</p>
                </div>
                <form className="catalog-search" onSubmit={handleSearch}>
                    <Search size={16} />
                    <input
                        value={inputVal}
                        onChange={(e) => setInputVal(e.target.value)}
                        placeholder="Filter products…"
                    />
                </form>
            </div>

            {loading ? (
                <Loader text="Loading products…" />
            ) : (
                <>
                    <motion.div className="catalog-grid" layout>
                        <AnimatePresence>
                            {products.map((p, i) => (
                                <ProductCard key={p.id} product={p} index={i} />
                            ))}
                        </AnimatePresence>
                    </motion.div>

                    <div className="catalog-pagination">
                        <button
                            disabled={meta.page <= 1}
                            onClick={() => load(meta.page - 1)}
                        >
                            <ChevronLeft size={18} /> Prev
                        </button>
                        <span>
                            Page {meta.page} of {meta.total_pages}
                        </span>
                        <button
                            disabled={meta.page >= meta.total_pages}
                            onClick={() => load(meta.page + 1)}
                        >
                            Next <ChevronRight size={18} />
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
