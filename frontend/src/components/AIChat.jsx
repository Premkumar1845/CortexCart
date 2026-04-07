import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Sparkles } from 'lucide-react';
import { getAIRecommendation } from '../services/api';
import './AIChat.css';

export default function AIChat() {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hi! I\'m CortexCart AI. Ask me for product recommendations — e.g. "Suggest luxury watches under $5000" or "Best designer handbags for women".' },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const handleSend = async (e) => {
        e.preventDefault();
        const msg = input.trim();
        if (!msg || loading) return;

        setMessages((prev) => [...prev, { role: 'user', content: msg }]);
        setInput('');
        setLoading(true);

        try {
            const reply = await getAIRecommendation(msg);
            setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
        } catch {
            setMessages((prev) => [...prev, { role: 'error', content: 'Something went wrong. Please try again.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <AnimatePresence>
                {open && (
                    <motion.div
                        className="ai-chat-panel"
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="ai-chat-header">
                            <div className="ai-chat-header-left">
                                <Sparkles size={18} />
                                <h3>CortexCart AI</h3>
                            </div>
                            <button className="ai-chat-close" onClick={() => setOpen(false)}>
                                <X size={18} />
                            </button>
                        </div>

                        <div className="ai-chat-messages">
                            {messages.map((m, i) => (
                                <div key={i} className={`ai-msg ${m.role}`}>
                                    {m.content}
                                </div>
                            ))}
                            {loading && (
                                <div className="ai-chat-typing">
                                    <span /><span /><span />
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        <form className="ai-chat-input" onSubmit={handleSend}>
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask for recommendations…"
                                disabled={loading}
                            />
                            <button className="ai-chat-send" type="submit" disabled={loading || !input.trim()}>
                                <Send size={16} />
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.button
                className="ai-chat-toggle"
                onClick={() => setOpen(!open)}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
            >
                {open ? <X size={24} /> : <MessageCircle size={24} />}
            </motion.button>
        </>
    );
}
