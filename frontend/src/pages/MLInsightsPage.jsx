import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    Brain, Layers, Cpu, Network, Activity, FlaskConical,
    Sparkles, TrendingUp, BarChart3, Zap, Hash, Tag, DollarSign,
} from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    CartesianGrid, Legend,
} from 'recharts';
import Loader from '../components/Loader';
import Particles from '../components/Particles';
import { getMLArchitecture, getMLMetrics, classifyProduct } from '../services/api';
import './MLInsightsPage.css';

const MODALITY_ICONS = {
    text: <Hash size={18} />,
    brand: <Tag size={18} />,
    price: <DollarSign size={18} />,
};

export default function MLInsightsPage() {
    const [architecture, setArchitecture] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [loadingArch, setLoadingArch] = useState(true);
    const [loadingMetrics, setLoadingMetrics] = useState(true);

    const [form, setForm] = useState({
        text: 'Automatic stainless steel chronograph wristwatch with sapphire crystal',
        brand: 'Tag Heuer',
        price: 2450,
        discount_pct: 12,
    });
    const [prediction, setPrediction] = useState(null);
    const [predicting, setPredicting] = useState(false);
    const [predictError, setPredictError] = useState('');

    useEffect(() => {
        (async () => {
            try {
                setArchitecture(await getMLArchitecture());
            } catch (e) {
                console.error(e);
            } finally {
                setLoadingArch(false);
            }
        })();
        (async () => {
            try {
                setMetrics(await getMLMetrics());
            } catch (e) {
                console.error(e);
            } finally {
                setLoadingMetrics(false);
            }
        })();
    }, []);

    const handlePredict = async (e) => {
        e.preventDefault();
        setPredicting(true);
        setPredictError('');
        try {
            const res = await classifyProduct(form);
            setPrediction(res);
        } catch (err) {
            setPredictError(err?.response?.data?.error || err.message || 'Prediction failed');
        } finally {
            setPredicting(false);
        }
    };

    const metricChartData = (metrics?.models || []).map((m) => ({
        name: m.label.length > 22 ? m.label.slice(0, 22) + '…' : m.label,
        Accuracy: +(m.accuracy * 100).toFixed(2),
        Precision: +(m.precision * 100).toFixed(2),
        Recall: +(m.recall * 100).toFixed(2),
        F1: +(m.f1 * 100).toFixed(2),
    }));

    return (
        <div className="ml-insights">
            <Particles count={22} />

            {/* ─── Hero ────────────────────────────────────────────── */}
            <section className="ml-hero">
                <div className="container">
                    <motion.span
                        className="ml-badge"
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <Sparkles size={14} /> ML Pipeline — Final Report Architecture
                    </motion.span>
                    <motion.h1
                        initial={{ opacity: 0, y: 18 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                    >
                        Multi-Modal <span className="gradient-text">Stacking Ensemble</span>
                    </motion.h1>
                    <motion.p
                        className="ml-sub"
                        initial={{ opacity: 0, y: 18 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        HashingVectorizer text features + LabelEncoded brand + StandardScaled pricing,
                        fused into a stacking ensemble of GBC · LightGBM · NGBoost with a
                        Calibrated LinearSVC meta-learner.
                    </motion.p>
                </div>
            </section>

            {/* ─── Architecture diagram ──────────────────────────────── */}
            <section className="ml-section container">
                <h2 className="ml-h2"><Network size={22} /> Pipeline Architecture</h2>
                {loadingArch ? (
                    <Loader text="Loading architecture…" />
                ) : !architecture ? (
                    <p className="ml-error">Architecture metadata unavailable.</p>
                ) : (
                    <>
                        <div className="ml-flow">
                            <div className="ml-flow-col ml-flow-inputs">
                                <div className="ml-flow-title">Inputs</div>
                                {architecture.feature_extractors.map((fe) => (
                                    <div className="ml-node ml-node-input" key={fe.name}>
                                        <div className="ml-node-icon">
                                            {MODALITY_ICONS[fe.modality] || <Layers size={18} />}
                                        </div>
                                        <div>
                                            <div className="ml-node-title">{fe.name}</div>
                                            <div className="ml-node-sub">{fe.modality}</div>
                                            <div className="ml-node-meta">
                                                {Object.entries(fe.config).map(([k, v]) => (
                                                    <span key={k}><code>{k}</code>={String(Array.isArray(v) ? `(${v.join(',')})` : v)}</span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="ml-flow-arrow">
                                <div className="ml-fusion-label">sparse hstack</div>
                                <div className="ml-arrow" />
                            </div>

                            <div className="ml-flow-col ml-flow-bases">
                                <div className="ml-flow-title">Base Estimators</div>
                                {architecture.base_estimators.map((b) => (
                                    <div className="ml-node ml-node-base" key={b.key}>
                                        <div className="ml-node-icon"><Cpu size={18} /></div>
                                        <div>
                                            <div className="ml-node-title">{b.label}</div>
                                            <div className="ml-node-sub">{b.library}</div>
                                            {b.note && <div className="ml-node-meta"><span>{b.note}</span></div>}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="ml-flow-arrow">
                                <div className="ml-fusion-label">stack</div>
                                <div className="ml-arrow" />
                            </div>

                            <div className="ml-flow-col ml-flow-meta">
                                <div className="ml-flow-title">Meta Learner</div>
                                <div className="ml-node ml-node-meta-est">
                                    <div className="ml-node-icon"><Brain size={18} /></div>
                                    <div>
                                        <div className="ml-node-title">
                                            {architecture.meta_estimator.name}
                                        </div>
                                        <div className="ml-node-sub">
                                            calibration: {architecture.meta_estimator.calibration} · cv: {architecture.meta_estimator.cv}
                                        </div>
                                    </div>
                                </div>
                                <div className="ml-node ml-node-output">
                                    <div className="ml-node-icon"><Zap size={18} /></div>
                                    <div>
                                        <div className="ml-node-title">Calibrated Probabilities</div>
                                        <div className="ml-node-sub">per product type</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="ml-arch-meta">
                            <span><strong>Fusion:</strong> <code>{architecture.fusion}</code></span>
                            <span><strong>Split:</strong> stratified test_size={architecture.training_split.test_size}</span>
                            <span><strong>Cache:</strong> <code>{architecture.deployment_notes.cache_dir}</code></span>
                        </div>
                    </>
                )}
            </section>

            {/* ─── Metrics ───────────────────────────────────────────── */}
            <section className="ml-section container">
                <h2 className="ml-h2"><BarChart3 size={22} /> Model Performance</h2>
                {loadingMetrics ? (
                    <Loader text="Loading metrics…" />
                ) : !metrics || !metrics.models?.length ? (
                    <p className="ml-error">No metrics available yet — train the pipeline first.</p>
                ) : (
                    <>
                        <div className="ml-metrics-summary">
                            <div className="ml-stat">
                                <span>Training Samples</span>
                                <strong>{metrics.samples_train?.toLocaleString()}</strong>
                            </div>
                            <div className="ml-stat">
                                <span>Test Samples</span>
                                <strong>{metrics.samples_test?.toLocaleString()}</strong>
                            </div>
                            <div className="ml-stat">
                                <span>Classes</span>
                                <strong>{metrics.classes?.length}</strong>
                            </div>
                            <div className="ml-stat">
                                <span>Feature Dim</span>
                                <strong>{metrics.feature_dim?.toLocaleString()}</strong>
                            </div>
                            <div className="ml-stat">
                                <span>Train Time</span>
                                <strong>{metrics.duration_seconds}s</strong>
                            </div>
                        </div>

                        <div className="ml-chart-wrap">
                            <ResponsiveContainer width="100%" height={340}>
                                <BarChart data={metricChartData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                    <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                                    <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} domain={[0, 100]} />
                                    <Tooltip
                                        contentStyle={{
                                            background: 'var(--surface-2)',
                                            border: '1px solid var(--border-soft)',
                                            borderRadius: 8,
                                        }}
                                    />
                                    <Legend />
                                    <Bar dataKey="Accuracy" fill="#6c5ce7" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Precision" fill="#00cec9" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="Recall" fill="#feca57" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="F1" fill="#fd79a8" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="ml-model-grid">
                            {metrics.models.map((m) => (
                                <div className={`ml-model-card ${m.available ? '' : 'unavailable'}`} key={m.name}>
                                    <div className="ml-model-head">
                                        <Activity size={16} />
                                        <strong>{m.label}</strong>
                                    </div>
                                    <div className="ml-model-grid-stats">
                                        <div><span>Acc</span><b>{(m.accuracy * 100).toFixed(2)}%</b></div>
                                        <div><span>Prec</span><b>{(m.precision * 100).toFixed(2)}%</b></div>
                                        <div><span>Recall</span><b>{(m.recall * 100).toFixed(2)}%</b></div>
                                        <div><span>F1</span><b>{(m.f1 * 100).toFixed(2)}%</b></div>
                                    </div>
                                    {m.note && <p className="ml-model-note">{m.note}</p>}
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </section>

            {/* ─── Live classifier playground ────────────────────────── */}
            <section className="ml-section container">
                <h2 className="ml-h2"><FlaskConical size={22} /> Live Classifier Playground</h2>
                <p className="ml-section-sub">
                    Enter product details and watch each base model and the stacking ensemble
                    return calibrated class probabilities in real time.
                </p>

                <div className="ml-playground">
                    <form className="ml-form" onSubmit={handlePredict}>
                        <label>
                            <span>Product description</span>
                            <textarea
                                rows={4}
                                value={form.text}
                                onChange={(e) => setForm({ ...form, text: e.target.value })}
                                placeholder="Describe the product (name + description)…"
                                required
                            />
                        </label>
                        <div className="ml-form-row">
                            <label>
                                <span>Brand</span>
                                <input
                                    type="text"
                                    value={form.brand}
                                    onChange={(e) => setForm({ ...form, brand: e.target.value })}
                                />
                            </label>
                            <label>
                                <span>Price (USD)</span>
                                <input
                                    type="number"
                                    min="0"
                                    value={form.price}
                                    onChange={(e) => setForm({ ...form, price: +e.target.value })}
                                />
                            </label>
                            <label>
                                <span>Discount %</span>
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    value={form.discount_pct}
                                    onChange={(e) => setForm({ ...form, discount_pct: +e.target.value })}
                                />
                            </label>
                        </div>
                        <button type="submit" className="ml-btn-primary" disabled={predicting}>
                            {predicting ? 'Classifying…' : (<><TrendingUp size={16} /> Run Pipeline</>)}
                        </button>
                        {predictError && <p className="ml-error">{predictError}</p>}
                    </form>

                    <div className="ml-results">
                        {prediction?.ensemble && (
                            <div className="ml-ensemble-card">
                                <div className="ml-ensemble-head">
                                    <Brain size={18} />
                                    <span>Ensemble Verdict</span>
                                </div>
                                <div className="ml-ensemble-class">
                                    {prediction.ensemble.predicted_class || '—'}
                                </div>
                                <div className="ml-ensemble-conf">
                                    confidence {(prediction.ensemble.confidence * 100).toFixed(1)}%
                                </div>
                                <div className="ml-prob-bars">
                                    {(prediction.ensemble.top || []).map((t) => (
                                        <div className="ml-prob-row" key={t.class}>
                                            <span>{t.class}</span>
                                            <div className="ml-prob-track">
                                                <div
                                                    className="ml-prob-fill"
                                                    style={{ width: `${Math.max(2, t.prob * 100)}%` }}
                                                />
                                            </div>
                                            <b>{(t.prob * 100).toFixed(1)}%</b>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {prediction?.per_model && Object.entries(prediction.per_model).map(([k, v]) => (
                            <div className="ml-base-card" key={k}>
                                <div className="ml-base-head"><Cpu size={14} /> {v.label}</div>
                                {v.error ? (
                                    <p className="ml-error">{v.error}</p>
                                ) : (
                                    <div className="ml-prob-bars compact">
                                        {(v.top || []).slice(0, 3).map((t) => (
                                            <div className="ml-prob-row" key={t.class}>
                                                <span>{t.class}</span>
                                                <div className="ml-prob-track">
                                                    <div
                                                        className="ml-prob-fill alt"
                                                        style={{ width: `${Math.max(2, t.prob * 100)}%` }}
                                                    />
                                                </div>
                                                <b>{(t.prob * 100).toFixed(1)}%</b>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                        {!prediction && (
                            <div className="ml-empty">
                                Submit a product to see per-model probability breakdowns.
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}
