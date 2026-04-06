import React from 'react';
import { motion } from 'framer-motion';
import './Loader.css';

export default function Loader({ text = 'Generating recommendations…' }) {
    return (
        <div className="loader-container">
            <div className="loader-rings">
                <motion.div
                    className="loader-ring ring-outer"
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
                />
                <motion.div
                    className="loader-ring ring-middle"
                    animate={{ rotate: -360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
                />
                <motion.div
                    className="loader-ring ring-inner"
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
                />
                <div className="loader-core" />
            </div>
            <motion.p
                className="loader-text"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
            >
                {text}
            </motion.p>
        </div>
    );
}
