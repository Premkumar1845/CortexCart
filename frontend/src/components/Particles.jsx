import React, { useMemo } from 'react';

/**
 * Decorative floating particle background.
 * Pure-CSS animation; lightweight; does not capture pointer events.
 *
 * Logic adapted from RecoML hero treatment: a small number of slowly-drifting
 * gold dots layered behind page content for a premium feel.
 */
export default function Particles({ count = 24 }) {
    const items = useMemo(
        () =>
            Array.from({ length: count }, (_, i) => ({
                left: (i * 37) % 100,
                top: (i * 53) % 100,
                delay: ((i * 0.4) % 3).toFixed(2),
                size: i % 3 === 0 ? 3 : i % 2 === 0 ? 2 : 1,
                alt: i % 4 === 0,
            })),
        [count]
    );

    return (
        <div className="particles-bg" aria-hidden="true">
            {items.map((p, i) => (
                <span
                    key={i}
                    className={`particle${p.alt ? ' alt' : ''}`}
                    style={{
                        left: `${p.left}%`,
                        top: `${p.top}%`,
                        width: `${p.size}px`,
                        height: `${p.size}px`,
                        animationDelay: `${p.delay}s`,
                    }}
                />
            ))}
        </div>
    );
}
