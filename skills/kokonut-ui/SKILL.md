---
name: kokonut-ui
description: Modern Tailwind CSS, Framer Motion, and Lucide React UI component blueprints inspired by Kokonut UI (kokonut-labs/kokonutui). Covers Dynamic Island navigation, modern AI input bars, Bento Grid cards, and interactive status buttons.
when-to-use:
  - kokonut ui
  - kokonutui
  - dynamic island
  - ai input
  - bento grid
  - modern tailwind components
  - action button
  - floating dock
user-invocable: true
argument-hint: "[component name or layout]"
---

# Kokonut UI Component Engineering

Kokonut UI is a sleek open-source component system built with **Tailwind CSS**, **shadcn/ui**, and **Motion** (Framer Motion / Motion for React), created by Kokonut Labs.

Use these verified patterns to build modern SaaS interfaces, landing pages, and interactive dashboards.

---

## 1. Dynamic Island / Floating Navigation Dock

A compact, pill-shaped floating command dock with micro-scale spring physics on hover:

```tsx
import React, { useState } from 'react';
import { Home, Compass, Bell, User, Sparkles } from 'lucide-react';

interface NavItem {
  icon: React.ElementType;
  label: string;
  id: string;
}

const NAV_ITEMS: NavItem[] = [
  { icon: Home, label: 'Home', id: 'home' },
  { icon: Compass, label: 'Explore', id: 'explore' },
  { icon: Sparkles, label: 'AI Studio', id: 'ai' },
  { icon: Bell, label: 'Alerts', id: 'alerts' },
  { icon: User, label: 'Profile', id: 'profile' },
];

export const DynamicIslandNav: React.FC = () => {
  const [active, setActive] = useState('home');

  return (
    <nav className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-1.5 p-2 rounded-full bg-neutral-900/90 backdrop-blur-xl border border-neutral-800 shadow-2xl shadow-black/50">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              className={`relative px-4 py-2.5 rounded-full flex items-center gap-2 text-sm font-medium transition-all duration-300 ${
                isActive
                  ? 'text-white bg-neutral-800 shadow-inner'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
              }`}
            >
              <Icon className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span>{item.label}</span>
              {isActive && (
                <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)]" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
```

---

## 2. Modern AI Prompt Input Bar

An interactive, expanding AI command box with file attachment support, token pill, and submit pulse:

```tsx
import React, { useState } from 'react';
import { Paperclip, ArrowUp, Sparkles, Globe } from 'lucide-react';

export const AIPromptInput: React.FC<{ onSubmit: (prompt: string) => void }> = ({ onSubmit }) => {
  const [input, setInput] = useState('');
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && input.trim()) {
      e.preventDefault();
      onSubmit(input);
      setInput('');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto rounded-2xl bg-neutral-900/90 border border-neutral-800/90 p-3 shadow-2xl focus-within:border-sky-500/50 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything or request creative components..."
        rows={2}
        className="w-full resize-none bg-transparent text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none px-2 py-1"
      />
      
      <div className="flex items-center justify-between pt-2 border-t border-neutral-800/60">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition"
            title="Attach file"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          
          <button
            type="button"
            onClick={() => setWebSearchEnabled(!webSearchEnabled)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition ${
              webSearchEnabled
                ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                : 'text-neutral-500 hover:bg-neutral-800'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Search</span>
          </button>
        </div>

        <button
          type="button"
          onClick={() => {
            if (input.trim()) {
              onSubmit(input);
              setInput('');
            }
          }}
          disabled={!input.trim()}
          className="p-2 rounded-xl bg-sky-500 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-sky-400 transition shadow-lg shadow-sky-500/25"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
```

---

## 3. Bento Grid Feature Card with Dynamic Hover Glow

```tsx
import React from 'react';

export const BentoCard: React.FC<{
  title: string;
  description: string;
  tag: string;
  visual: React.ReactNode;
}> = ({ title, description, tag, visual }) => {
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-neutral-800/90 bg-neutral-900/60 p-6 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-neutral-700 hover:shadow-2xl">
      <div className="mb-4 inline-flex items-center rounded-full border border-neutral-700 bg-neutral-800/60 px-3 py-1 text-xs font-semibold text-neutral-300">
        {tag}
      </div>
      <h3 className="text-xl font-bold tracking-tight text-white mb-2">{title}</h3>
      <p className="text-sm text-neutral-400 leading-relaxed mb-6">{description}</p>
      <div className="relative overflow-hidden rounded-2xl bg-neutral-950/80 border border-neutral-800 p-4">
        {visual}
      </div>
    </div>
  );
};
```
