---
name: react-bits
description: Production-grade component blueprints and animation patterns from React Bits (DavidHDev/react-bits). Covers animated backgrounds (Aurora, Hyperspeed, Dot Grid), text effects (Decrypted Text, Blur Text, Shiny Text), and micro-interactions (Spotlight Card, Magnet, Tilt).
when-to-use:
  - react bits
  - react-bits
  - animated background
  - decrypted text
  - shiny text
  - blur text
  - spotlight card
  - tilt card
  - click spark
  - aurora background
  - modern react animations
user-invocable: true
argument-hint: "[component name or animation effect]"
---

# React Bits Animation & Component Engine

React Bits is an elite open-source collection of copy-paste React components and micro-interactions created by David Haz (@DavidHDev).

Use these verified patterns in React, Vite, Next.js, or Tailwind CSS projects to add high-impact animations with minimal dependencies.

---

## 1. Text Animation Blueprints

### A. Decrypted Text (Cyberpunk / Hacker Scramble on Hover or Mount)
Scrambles letters into random ASCII glyphs before resolving to the target word:

```tsx
import React, { useState, useEffect } from 'react';

interface DecryptedTextProps {
  text: string;
  speed?: number;
  characters?: string;
  className?: string;
}

export const DecryptedText: React.FC<DecryptedTextProps> = ({
  text,
  speed = 45,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()',
  className = ''
}) => {
  const [displayText, setDisplayText] = useState(text);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split('')
          .map((char, index) => {
            if (index < iteration) return text[index];
            if (char === ' ') return ' ';
            return characters[Math.floor(Math.random() * characters.length)];
          })
          .join('')
      );

      if (iteration >= text.length) {
        clearInterval(interval);
      }
      iteration += 1 / 3;
    }, speed);

    return () => clearInterval(interval);
  }, [text, isHovered, speed, characters]);

  return (
    <span
      className={`font-mono inline-block cursor-default select-none ${className}`}
      onMouseEnter={() => setIsHovered(prev => !prev)}
    >
      {displayText}
    </span>
  );
};
```

### B. Shiny Text (Animated High-End Metallic Gradient Shimmer)
```tsx
import React from 'react';

export const ShinyText: React.FC<{ text: string; disabled?: boolean; speed?: number; className?: string }> = ({
  text,
  disabled = false,
  speed = 5,
  className = ''
}) => {
  return (
    <span
      className={`inline-block bg-clip-text text-transparent bg-gradient-to-r from-neutral-400 via-white to-neutral-400 bg-[length:200%_100%] ${
        disabled ? '' : 'animate-shimmer'
      } ${className}`}
      style={{ animationDuration: `${speed}s` }}
    >
      {text}
    </span>
  );
};

// Add to tailwind.config.js or style.css:
// @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
// .animate-shimmer { animation: shimmer 5s linear infinite; }
```

---

## 2. Interactive Card Blueprints

### Spotlight Card (Cursor-Tracking Radial Glow Border)
Renders a dynamic border and surface highlight that follows the cursor coordinates:

```tsx
import React, { useRef, useState } from 'react';

interface SpotlightCardProps {
  children: React.ReactNode;
  className?: string;
  spotlightColor?: string;
}

export const SpotlightCard: React.FC<SpotlightCardProps> = ({
  children,
  className = '',
  spotlightColor = 'rgba(56, 189, 248, 0.25)'
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    setOpacity(1);
  };

  const handleMouseLeave = () => {
    setOpacity(0);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/80 p-8 shadow-2xl transition-all duration-300 hover:border-neutral-700 ${className}`}
    >
      {/* Dynamic Cursor Spotlight Radial Background */}
      <div
        className="pointer-events-none absolute -inset-px transition-opacity duration-300"
        style={{
          opacity,
          background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 40%)`
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
};
```

---

## 3. High-Performance Canvas Backgrounds

### Interactive Dot Grid Canvas (Low GPU / CPU Footprint)
```tsx
import React, { useEffect, useRef } from 'react';

export const DotGridBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    const spacing = 32;
    let mouse = { x: -1000, y: -1000 };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);

    let animationId: number;
    const render = () => {
      ctx.clearRect(0, 0, width, height);

      for (let x = spacing / 2; x < width; x += spacing) {
        for (let y = spacing / 2; y < height; y += spacing) {
          const dx = mouse.x - x;
          const dy = mouse.y - y;
          const dist = Math.hypot(dx, dy);
          const maxDist = 140;

          let radius = 1.2;
          let alpha = 0.2;

          if (dist < maxDist) {
            const factor = 1 - dist / maxDist;
            radius = 1.2 + factor * 2.2;
            alpha = 0.2 + factor * 0.7;
          }

          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.fill();
        }
      }
      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0" />;
};
```
