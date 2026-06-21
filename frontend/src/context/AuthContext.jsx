import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import {
    apiLogin,
    apiLogout,
    apiMe,
    apiSignup,
    setAuthToken,
} from '../services/api';

const AuthContext = createContext(null);
const TOKEN_KEY = 'cortexcart_token';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null);
    const [loading, setLoading] = useState(true);

    // Hydrate user on first load
    useEffect(() => {
        let cancelled = false;
        const hydrate = async () => {
            if (token) {
                setAuthToken(token);
                try {
                    const data = await apiMe();
                    if (!cancelled) setUser(data.user || null);
                } catch {
                    if (!cancelled) {
                        setUser(null);
                        setToken(null);
                        localStorage.removeItem(TOKEN_KEY);
                        setAuthToken(null);
                    }
                }
            }
            if (!cancelled) setLoading(false);
        };
        hydrate();
        return () => { cancelled = true; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const persistAuth = useCallback((nextToken, nextUser) => {
        setToken(nextToken);
        setUser(nextUser);
        if (nextToken) {
            localStorage.setItem(TOKEN_KEY, nextToken);
            setAuthToken(nextToken);
        } else {
            localStorage.removeItem(TOKEN_KEY);
            setAuthToken(null);
        }
    }, []);

    const login = useCallback(async (username, password) => {
        const data = await apiLogin(username, password);
        persistAuth(data.token, data.user);
        return data.user;
    }, [persistAuth]);

    const signup = useCallback(async (payload) => {
        const data = await apiSignup(payload);
        persistAuth(data.token, data.user);
        return data.user;
    }, [persistAuth]);

    const logout = useCallback(async () => {
        try { await apiLogout(); } catch { /* ignore */ }
        persistAuth(null, null);
    }, [persistAuth]);

    const value = {
        user,
        token,
        loading,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        login,
        signup,
        logout,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
}
