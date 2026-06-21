import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogIn } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

export default function LoginPage() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from || '/';
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setError('');
        setBusy(true);
        try {
            const u = await login(username.trim(), password);
            navigate(u.role === 'admin' ? '/admin' : from, { replace: true });
        } catch (err) {
            setError(err?.response?.data?.error || err?.message || 'Login failed');
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="auth-wrap container">
            <motion.form
                className="auth-card"
                onSubmit={submit}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
            >
                <div className="auth-icon"><LogIn size={28} /></div>
                <h1 className="auth-title">Welcome back</h1>
                <p className="auth-sub">Sign in to your CortexCart account.</p>

                {error && <div className="auth-error">{error}</div>}

                <label className="auth-label">Username
                    <input
                        autoFocus
                        autoComplete="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </label>
                <label className="auth-label">Password
                    <input
                        type="password"
                        autoComplete="current-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </label>

                <button className="auth-btn" type="submit" disabled={busy}>
                    {busy ? 'Signing in…' : 'Sign in'}
                </button>

                <p className="auth-foot">
                    No account? <Link to="/signup">Create one</Link>
                </p>
            </motion.form>
        </div>
    );
}
