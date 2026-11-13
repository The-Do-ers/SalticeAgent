---
name: creative-web-design
description: Architectural patterns and animation blueprints derived from award-winning creative websites (Niccolò Miranda, Danilo De Marco, Bleibt Gleich, 2xA Studio, Thibaut Foussier, Bulbs, Ollivere). Covers editorial typography, paper noise shaders, horizontal parallax scrub, 2D/3D physics playgrounds, and stacked card decks.
when-to-use:
  - creative website
  - awwwards
  - niccolo miranda
  - danilo demarco
  - blijftgleich
  - 2xa studio
  - thibaut cool
  - bulbs
  - ollivere
  - creative portfolio
  - paper texture
  - physics playground
  - stacked cards
user-invocable: true
argument-hint: "[site style or effect name]"
---

# Creative Web Design & Interaction Blueprints

This skill captures the signature engineering techniques, interaction mechanics, and visual stacks behind 7 award-winning creative portfolios and design studios.

---

## 1. Niccolò Miranda Narrative Style (`niccolomiranda.com`)

### Key Characteristics:
- Editorial detective/newspaper narrative with rich storytelling.
- Procedural paper grain/film noise texture overlay across the viewport.
- Pinned multi-scene chapters driven by GSAP ScrollTrigger timelines.
- Custom interactive cursor with direction-aware rotation and scale on interactive targets.

### Implementation Blueprint:
```html
<!-- 1. Zero-Asset SVG Procedural Film Grain Overlay -->
<div class="grain-overlay"></div>
<style>
.grain-overlay {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9999;
    opacity: 0.045;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}
</style>
```

```javascript
// 2. Multi-Scene Chapter Timeline with Pinning
function initChapterStoryline() {
    const tl = gsap.timeline({
        scrollTrigger: {
            trigger: "#chapter-1",
            start: "top top",
            end: "+=1800",
            scrub: 1,
            pin: true
        }
    });

    tl.from(".chapter-headline", { yPercent: 100, opacity: 0, duration: 1 })
      .to(".chapter-illustration", { scale: 1.15, rotation: 2, duration: 1.5 }, "<")
      .to(".chapter-paragraph", { opacity: 1, y: 0, stagger: 0.2, duration: 1 });
}
```

---

## 2. Danilo De Marco Monochrome Typography (`danilodemarco.com`)

### Key Characteristics:
- High-contrast black, white, and raw concrete grayscale palette.
- Massive editorial serif/sans display headlines with fluid viewport clamping (`clamp(2.5rem, 8vw, 9rem)`).
- Liquid texture hover distortion over project imagery.
- Magnetic interactive anchor pills.

### Implementation Blueprint:
```css
/* Fluid Typography with Zero Breakpoint Jitter */
.editorial-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3rem, 10vw, 9.5rem);
    line-height: 0.88;
    letter-spacing: -0.04em;
    font-weight: 700;
    text-transform: uppercase;
}

/* Concrete Contrast Palette */
:root {
    --bg-dark: #0a0a0c;
    --text-primary: #f5f5f7;
    --text-muted: #73737a;
    --accent-silver: #d4d4d8;
}
```

---

## 3. Bleibt Gleich Horizontal Scrub (`bleibtgleich.dev`)

### Key Characteristics:
- Pinned viewport horizontal scroll scrub across showcase panels.
- Scroll velocity dynamically expands headline letter-spacing.
- Dark obsidian depth with ambient cyan/purple accent lighting.

### Implementation Blueprint:
```javascript
function initHorizontalShowcase() {
    const panels = gsap.utils.toArray(".project-panel");
    const container = document.querySelector(".horizontal-wrapper");

    gsap.to(panels, {
        xPercent: -100 * (panels.length - 1),
        ease: "none",
        scrollTrigger: {
            trigger: container,
            pin: true,
            scrub: 1,
            snap: 1 / (panels.length - 1),
            end: () => `+=${container.offsetWidth}`
        }
    });

    // Velocity-reactive letter-spacing expansion
    let lastScroll = window.scrollY;
    ScrollTrigger.create({
        onUpdate: (self) => {
            const velocity = Math.abs(self.getVelocity() / 300);
            gsap.to(".dynamic-spacing", {
                letterSpacing: `${Math.min(18, 2 + velocity)}px`,
                duration: 0.2,
                ease: "power1.out"
            });
        }
    });
}
```

---

## 4. 2xA Studio Polygon Mask Reveal (`2xa.studio`)

### Key Characteristics:
- High-fashion avant-garde grid layouts.
- Geometric `clip-path` mask reveals on scroll.
- Seamless marquee ticker ribbons.

### Implementation Blueprint:
```javascript
function initClipPathReveals() {
    gsap.fromTo(".mask-reveal", 
        { clipPath: "polygon(0 100%, 100% 100%, 100% 100%, 0 100%)" },
        {
            clipPath: "polygon(0 0%, 100% 0%, 100% 100%, 0 100%)",
            duration: 1.2,
            ease: "power3.inOut",
            scrollTrigger: {
                trigger: ".mask-reveal",
                start: "top 75%"
            }
        }
    );
}
```

---

## 5. Thibaut Foussier & Bulbs Physics Playgrounds (`thibaut.cool` & `bulbs.simondupety.com`)

### Key Characteristics:
- Interactive 2D/3D physics simulation right in the viewport.
- Elements (pills, logos, lightbulbs) fall with gravity, collide, and can be dragged/thrown by the user.

### Implementation Blueprint (Matter.js 2D Physics Canvas):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/matter-js/0.19.0/matter.min.js"></script>
<script>
function initPhysicsPlayground(containerId) {
    const { Engine, Render, Runner, Bodies, Composite, Mouse, MouseConstraint } = Matter;

    const engine = Engine.create();
    const render = Render.create({
        element: document.getElementById(containerId),
        engine: engine,
        options: { width: window.innerWidth, height: 600, wireframes: false, background: 'transparent' }
    });

    // Ground and Boundaries
    const ground = Bodies.rectangle(window.innerWidth / 2, 610, window.innerWidth, 20, { isStatic: true });
    const leftWall = Bodies.rectangle(-10, 300, 20, 600, { isStatic: true });
    const rightWall = Bodies.rectangle(window.innerWidth + 10, 300, 20, 600, { isStatic: true });

    // Interactive Floating Bouncy Pills
    const pills = Array.from({ length: 12 }, (_, i) => {
        return Bodies.rectangle(200 + i * 50, 50, 120, 44, {
            chamfer: { radius: 22 },
            restitution: 0.8, // Bouncy elasticity
            render: { fillStyle: i % 2 === 0 ? '#38bdf8' : '#818cf8' }
        });
    });

    Composite.add(engine.world, [ground, leftWall, rightWall, ...pills]);

    // Mouse Drag Constraint
    const mouse = Mouse.create(render.canvas);
    const mouseConstraint = MouseConstraint.create(engine, { mouse: mouse });
    Composite.add(engine.world, mouseConstraint);

    Render.run(render);
    Runner.run(Runner.create(), engine);
}
</script>
```

---

## 6. Ollivere Stacked Card Deck (`ollivere.webflow.io`)

### Key Characteristics:
- Ultra-smooth Lenis inertia scrolling.
- Cards stack on top of each other, slightly scaling down and dimming as new cards slide in.

### Implementation Blueprint:
```javascript
function initStackedDeck() {
    const cards = gsap.utils.toArray(".deck-card");
    cards.forEach((card, i) => {
        if (i === cards.length - 1) return;
        ScrollTrigger.create({
            trigger: cards[i + 1],
            start: "top 70%",
            end: "top 15%",
            scrub: true,
            onUpdate: (self) => {
                const progress = self.progress;
                gsap.to(card, {
                    scale: 1 - progress * 0.08,
                    y: progress * 20,
                    opacity: 1 - progress * 0.5,
                    filter: `blur(${progress * 4}px)`,
                    overwrite: "auto"
                });
            }
        });
    });
}
```
