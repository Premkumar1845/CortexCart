import React from 'react';
import { motion } from 'framer-motion';
import { User, Shield, LogOut, Mail, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

export default function ProfilePage() {
    const { user, logout, isAdmin } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    if (!user) return null;

    return (
        <div className="auth-wrap container">
            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                style={{ maxWidth: 520 }}
            >
                <div className="auth-icon">{isAdmin ? <Shield size={28} /> : <User size={28} />}</div>
                <h1 className="auth-title">{user.full_name || user.username}</h1>
                <p className="auth-sub">@{user.username} · {isAdmin ? 'Administrator' : 'Member'}</p>

                <div style={{ display: 'grid', gap: 12, marginBottom: 24 }}>
                    {user.email && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-secondary)' }}>
                            <Mail size={16} /> <span>{user.email}</span>
                        </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-secondary)' }}>
                        <Calendar size={16} />
                        <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                    {user.last_login_at && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-secondary)' }}>
                            <Calendar size={16} />
                            <span>Last login {new Date(user.last_login_at).toLocaleString()}</span>
                        </div>
                    )}
                </div>

                {isAdmin && (
                    <button className="auth-btn" onClick={() => navigate('/admin')} style={{ marginBottom: 10 }}>
                        Open Admin Dashboard
                    </button>
                )}
                <button
                    className="auth-btn"
                    onClick={handleLogout}
                    style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239,68,68,0.4)', color: '#fca5a5' }}
                >
                    <LogOut size={16} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                    Sign out
                </button>
            </motion.div>
        </div>
    );
}
