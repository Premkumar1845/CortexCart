import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Sparkles, Menu, X } from 'lucide-react';
import './Navbar.css';

export default function Navbar() {
    const [query, setQuery] = useState('');
    const [menuOpen, setMenuOpen] = useState(false);
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/catalog?search=${encodeURIComponent(query.trim())}`);
            setQuery('');
        }
    };

    return (
        <motion.nav
            className="navbar"
            initial={{ y: -80 }}
            animate={{ y: 0 }}
            transition={{ type: 'spring', stiffness: 120, damping: 20 }}
        >
            <div className="navbar-inner container">
                <Link to="/" className="navbar-logo">
                    <Sparkles size={22} />
                    <span>CortexCart</span>
                </Link>

                <div className={`navbar-links ${menuOpen ? 'open' : ''}`}>
                    <Link to="/" onClick={() => setMenuOpen(false)}>Home</Link>
                    <Link to="/catalog" onClick={() => setMenuOpen(false)}>Explore</Link>
                    <Link to="/batch" onClick={() => setMenuOpen(false)}>Batch</Link>
                </div>

                <form className="navbar-search" onSubmit={handleSearch}>
                    <Search size={16} className="navbar-search-icon" />
                    <input
                        type="text"
                        placeholder="Search products…"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                </form>

                <button className="navbar-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
                    {menuOpen ? <X size={22} /> : <Menu size={22} />}
                </button>
            </div>
        </motion.nav>
    );
}
