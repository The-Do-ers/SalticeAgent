---
name: gsap-lenis-motion
description: Production-grade GreenSock (GSAP 3) and Lenis Smooth Scroll animation engine. Covers ScrollTrigger, timeline sequencing, kinetic typography, magnetic cursor physics, horizontal parallax, and Awwwards-grade creative web interactions.
when-to-use:
  - gsap
  - greensock
  - lenis
  - smooth scroll
  - scrolltrigger
  - kinetic typography
  - creative animation
  - magnetic button
  - page transitions
  - awards website
user-invocable: true
argument-hint: "[animation type or scroll effect]"
---

# GSAP & Lenis Creative Motion Engineering

This skill provides verified, zero-hang implementation patterns for **GSAP 3**, **ScrollTrigger**, and **Lenis Smooth Scroll**. Use these standards to create fluid, cinematic, awards-grade web experiences.

---

## 1. Core CDN & Modern ESM Dependencies

### Vanilla HTML / Single-File Web Apps:
```html
<!-- Lenis Smooth Scroll (Latest v1.1.18+) -->
<script src="https://unpkg.com/lenis@1.1.18/dist/lenis.min.js"></script>

<!-- GSAP 3 Core & Essential Plugins -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/Flip.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/Observer.min.js"></script>
```

### React / Next.js / Vite Projects:
```bash
npm install gsap lenis @studio-freight/lenis
```

---

## 2. Canonical Lenis + GSAP ScrollTrigger Synchronization

To prevent scroll jitter, tearing, or desync, Lenis and GSAP's internal ticker MUST be synchronized via the GSAP ticker. **Never run duplicate `requestAnimationFrame` loops for Lenis and GSAP.**

```javascript
// Register Plugin
gsap.registerPlugin(ScrollTrigger);

// Initialize Lenis
const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Exponential deceleration
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 1.0,
    touchMultiplier: 2.0,
    infinite: false
});

// Synchronize Lenis with GSAP ScrollTrigger
lenis.on('scroll', ScrollTrigger.update);

// Drive Lenis directly via GSAP's 60/120fps Ticker
gsap.ticker.add((time) => {
    lenis.raf(time * 1000);
});

// Disable lag smoothing to prevent animation jumps after tab inactivity
gsap.ticker.lagSmoothing(0);
```

---

## 3. Awards-Grade Motion Patterns

### A. Kinetic Typography & Staggered Reveal
Reveals text character-by-character or line-by-line from a masked baseline:

```javascript
function initTextReveal() {
    // Wrap characters in mask spans: <span class="overflow-hidden inline-block"><span class="char inline-block">A</span></span>
    gsap.from(".char", {
        scrollTrigger: {
            trigger: ".hero-title",
            start: "top 80%",
            toggleActions: "play none none reverse"
        },
        yPercent: 120,
        opacity: 0,
        rotateZ: 4,
        stagger: 0.02,
        duration: 0.85,
        ease: "power4.out"
    });
}
```

### B. Pin & Horizontal Scrub Section (Awwwards Style)
Pins the viewport and scrubs horizontally across child cards as the user scrolls vertically:

```javascript
function initHorizontalScrub() {
    const track = document.querySelector(".horizontal-track");
    const sections = gsap.utils.toArray(".horizontal-panel");

    gsap.to(sections, {
        xPercent: -100 * (sections.length - 1),
        ease: "none",
        scrollTrigger: {
            trigger: ".horizontal-container",
            pin: true,
            scrub: 1, // Smooth 1-second lag scrub
            snap: 1 / (sections.length - 1),
            start: "top top",
            end: () => `+=${track.scrollWidth - window.innerWidth}`
        }
    });
}
```

### C. Magnetic Cursor Button (Spring Attraction)
Attracts interactive buttons toward the cursor when within a proximity radius:

```javascript
function initMagneticButtons() {
    const magneticElements = document.querySelectorAll(".magnetic-btn");

    magneticElements.forEach((el) => {
        el.addEventListener("mousemove", (e) => {
            const rect = el.getBoundingClientRect();
            const x = (e.clientX - rect.left - rect.width / 2) * 0.35;
            const y = (e.clientY - rect.top - rect.height / 2) * 0.35;

            gsap.to(el, {
                x: x,
                y: y,
                duration: 0.3,
                ease: "power2.out"
            });
        });

        el.addEventListener("mouseleave", () => {
            gsap.to(el, {
                x: 0,
                y: 0,
                duration: 0.7,
                ease: "elastic.out(1.1, 0.4)"
            });
        });
    });
}
```

### D. Layered Stacked Cards (Ollivere & Apple Style)
Cards stack and scale down as subsequent cards scroll over them:

```javascript
function initStackedCards() {
    const cards = gsap.utils.toArray(".stacked-card");
    cards.forEach((card, index) => {
        if (index === cards.length - 1) return;
        gsap.to(card, {
            scale: 0.92 - (cards.length - index) * 0.02,
            opacity: 0.4,
            filter: "blur(6px)",
            scrollTrigger: {
                trigger: cards[index + 1],
                start: "top 80%",
                end: "top 20%",
                scrub: true
            }
        });
    });
}
```

---

## 4. Critical Performance Directives
1. **Always use CSS transform properties** (`x`, `y`, `scale`, `rotation`, `xPercent`, `yPercent`) rather than animating `top`, `left`, `width`, or `height` (which trigger browser layout reflow).
2. **Apply `will-change: transform`** on high-frequency animated elements.
3. In React/Vite, wrap animations in `gsap.context()` inside `useEffect` or `useGSAP()` to cleanly kill all ScrollTriggers on unmount and prevent memory leaks.
