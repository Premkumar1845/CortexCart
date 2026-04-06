import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, X, Download, CheckCircle, AlertCircle } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import Loader from '../components/Loader';
import { getBatchRecommendations, downloadBatchCSV } from '../services/api';
import './BatchPage.css';

export default function BatchPage() {
    const [file, setFile] = useState(null);
    const [dragging, setDragging] = useState(false);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const inputRef = useRef();

    const handleDrop = (e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files[0];
        if (f && f.name.endsWith('.csv')) {
            setFile(f);
            setError('');
        } else {
            setError('Please upload a CSV file');
        }
    };

    const handleFileChange = (e) => {
        const f = e.target.files[0];
        if (f) { setFile(f); setError(''); }
    };

    const handleSubmit = async () => {
        if (!file) return;
        setLoading(true);
        setError('');
        try {
            const data = await getBatchRecommendations(file, 5);
            setResults(data.recommendations);
        } catch (err) {
            setError('Failed to process batch. Check your CSV format.');
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadCSV = async () => {
        if (!file) return;
        try {
            const blob = await downloadBatchCSV(file, 5);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'recommendations.csv';
            a.click();
            URL.revokeObjectURL(url);
        } catch {
            setError('Download failed');
        }
    };

    return (
        <div className="batch container">
            <div className="batch-header">
                <h1>Batch Recommendations</h1>
                <p>Upload a CSV file with product queries to get bulk recommendations.</p>
            </div>

            <div className="batch-info">
                <h3>CSV Format</h3>
                <p>Your CSV should have a <code>query</code> column (required) and optionally a <code>brand</code> column:</p>
                <pre>query,brand{'\n'}omega speedmaster,Omega{'\n'}diamond ring,{'\n'}rolex submariner,Rolex</pre>
            </div>

            <motion.div
                className={`batch-dropzone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    hidden
                />
                <AnimatePresence mode="wait">
                    {file ? (
                        <motion.div
                            key="file"
                            className="batch-file-info"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <FileText size={32} />
                            <span>{file.name}</span>
                            <button
                                className="batch-remove"
                                onClick={(e) => { e.stopPropagation(); setFile(null); setResults(null); }}
                            >
                                <X size={16} />
                            </button>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="empty"
                            className="batch-empty"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <Upload size={40} />
                            <p>Drag & drop CSV here or click to browse</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

            {error && (
                <div className="batch-error">
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            <div className="batch-actions">
                <button className="batch-btn primary" onClick={handleSubmit} disabled={!file || loading}>
                    {loading ? 'Processing…' : 'Get Recommendations'}
                </button>
                {results && (
                    <button className="batch-btn secondary" onClick={handleDownloadCSV}>
                        <Download size={16} /> Download CSV
                    </button>
                )}
            </div>

            {loading && <Loader text="Processing batch queries…" />}

            {results && !loading && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <div className="batch-results-header">
                        <CheckCircle size={18} />
                        <h2>{results.length} recommendations generated</h2>
                    </div>
                    <div className="batch-results-grid">
                        {results.slice(0, 20).map((r, i) => (
                            <ProductCard key={`${r.id}-${i}`} product={r} index={i} />
                        ))}
                    </div>
                    {results.length > 20 && (
                        <p className="batch-more">
                            Showing 20 of {results.length} — download CSV for all results
                        </p>
                    )}
                </motion.div>
            )}
        </div>
    );
}
