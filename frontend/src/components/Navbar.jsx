import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Sparkles, Menu, X, User, Shield, LogIn, LogOut, UserPlus, Brain } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export default function Navbar() {
    const [query, setQuery] = useState('');
    const [menuOpen, setMenuOpen] = useState(false);
    const [accountOpen, setAccountOpen] = useState(false);
    const navigate = useNavigate();
    const { user, isAuthenticated, isAdmin, logout } = useAuth();

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/catalog?search=${encodeURIComponent(query.trim())}`);
            setQuery('');
        }
    };

    const handleLogout = async () => {
        setAccountOpen(false);
        await logout();
        navigate('/');
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
                    <Link to="/insights" onClick={() => setMenuOpen(false)} className="navbar-link-accent">
                        <Brain size={14} /> ML Insights
                    </Link>
                    {isAuthenticated && !isAdmin && (
                        <Link to="/dashboard" onClick={() => setMenuOpen(false)}>Dashboard</Link>
                    )}
                    {isAdmin && <Link to="/admin" onClick={() => setMenuOpen(false)}>Admin</Link>}
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

                {isAuthenticated ? (
                    <div className="navbar-account">
                        <button
                            className="navbar-account-btn"
                            onClick={() => setAccountOpen((v) => !v)}
                            aria-haspopup="menu"
                            aria-expanded={accountOpen}
                        >
                            {isAdmin ? <Shield size={16} /> : <User size={16} />}
                            <span>{user.username}</span>
                        </button>
                        {accountOpen && (
                            <div className="navbar-menu" role="menu" onMouseLeave={() => setAccountOpen(false)}>
                                <Link to="/profile" onClick={() => setAccountOpen(false)}>
                                    <User size={14} /> Profile
                                </Link>
                                {!isAdmin && (
                                    <Link to="/dashboard" onClick={() => setAccountOpen(false)}>
                                        <UserPlus size={14} /> Dashboard
                                    </Link>
                                )}
                                {isAdmin && (
                                    <Link to="/admin" onClick={() => setAccountOpen(false)}>
                                        <Shield size={14} /> Admin
                                    </Link>
                                )}
                                <button onClick={handleLogout}>
                                    <LogOut size={14} /> Sign out
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="navbar-auth">
                        <Link to="/login" className="navbar-auth-link">
                            <LogIn size={14} /> Login
                        </Link>
                        <Link to="/signup" className="navbar-auth-cta">
                            <UserPlus size={14} /> Sign up
                        </Link>
                    </div>
                )}

                <button className="navbar-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
                    {menuOpen ? <X size={22} /> : <Menu size={22} />}
                </button>
            </div>
        </motion.nav>
    );
}
