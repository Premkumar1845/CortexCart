import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Loader from './Loader';

export function RequireAuth({ children }) {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();
    if (loading) return <Loader />;
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }
    return children;
}

export function RequireAdmin({ children }) {
    const { isAuthenticated, isAdmin, loading } = useAuth();
    const location = useLocation();
    if (loading) return <Loader />;
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location.pathname }} replace />;
    }
    if (!isAdmin) {
        return <Navigate to="/" replace />;
    }
    return children;
}
