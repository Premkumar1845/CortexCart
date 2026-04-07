import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import AIChat from './components/AIChat';
import HomePage from './pages/HomePage';
import CatalogPage from './pages/CatalogPage';
import BatchPage from './pages/BatchPage';
import RecommendationsPage from './pages/RecommendationsPage';

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
                </Routes>
            </main>
            <AIChat />
        </div>
    );
}
