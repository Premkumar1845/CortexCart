import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthPages.css';

export default function SignupPage() {
    const { signup } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '' });
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const update = (k) => (e) => setForm((s) => ({ ...s, [k]: e.target.value }));

    const submit = async (e) => {
        e.preventDefault();
        setError('');
        setBusy(true);
        try {
            await signup({
                username: form.username.trim(),
                email: form.email.trim(),
                full_name: form.full_name.trim(),
                password: form.password,
            });
            navigate('/', { replace: true });
        } catch (err) {
            setError(err?.response?.data?.error || err?.message || 'Signup failed');
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
                <div className="auth-icon"><UserPlus size={28} /></div>
                <h1 className="auth-title">Create your account</h1>
                <p className="auth-sub">Get personalized AI recommendations.</p>

                {error && <div className="auth-error">{error}</div>}

                <label className="auth-label">Username
                    <input value={form.username} onChange={update('username')} required minLength={3} maxLength={32} pattern="[A-Za-z0-9_.\-]+" />
                </label>
                <label className="auth-label">Full name (optional)
                    <input value={form.full_name} onChange={update('full_name')} maxLength={80} />
                </label>
                <label className="auth-label">Email (optional)
                    <input type="email" value={form.email} onChange={update('email')} />
                </label>
                <label className="auth-label">Password
                    <input type="password" value={form.password} onChange={update('password')} required minLength={8} autoComplete="new-password" />
                </label>

                <button className="auth-btn" type="submit" disabled={busy}>
                    {busy ? 'Creating…' : 'Create account'}
                </button>

                <p className="auth-foot">
                    Already registered? <Link to="/login">Sign in</Link>
                </p>
            </motion.form>
        </div>
    );
}
