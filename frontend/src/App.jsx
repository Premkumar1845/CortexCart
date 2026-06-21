import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import AIChat from './components/AIChat';
import HomePage from './pages/HomePage';
import CatalogPage from './pages/CatalogPage';
import BatchPage from './pages/BatchPage';
import RecommendationsPage from './pages/RecommendationsPage';
import MLInsightsPage from './pages/MLInsightsPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import UserDashboard from './pages/UserDashboard';
import { RequireAuth, RequireAdmin } from './components/RouteGuards';

export default function App() {
    return (
        <div className="app">
            <Navbar />
            <main className="main-content">
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/catalog" element={<CatalogPage />} />
                    <Route path="/batch" element={<BatchPage />} />
                    <Route path="/recommendations/:id" element={<RecommendationsPage />} />
                    <Route path="/insights" element={<MLInsightsPage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/signup" element={<SignupPage />} />
                    <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
                    <Route path="/dashboard" element={<RequireAuth><UserDashboard /></RequireAuth>} />
                    <Route path="/admin" element={<RequireAdmin><AdminPage /></RequireAdmin>} />
                </Routes>
            </main>
            <AIChat />
        </div>
    );
}
