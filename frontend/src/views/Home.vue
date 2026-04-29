<template>
  <div class="home">
    <section class="hero">
      <img :src="heroImg" class="hero-img" :style="heroImageStyle" alt="E-waste awareness" />
      <div class="hero-overlay"></div>
      <div class="hero-gradient"></div>

      <div class="hero-content" :style="heroContentStyle">
        <p class="hero-tag">EcoTech</p>
        <h1>Dispose E-waste the Right Way</h1>
        <p class="hero-subtitle">
          Learn why e-waste is harmful, understand simple health risks, and find safe disposal
          options near you.
        </p>

        <div class="hero-actions">
          <router-link to="/disposal-locations" class="hero-btn primary">
            Find Disposal Sites
          </router-link>
          <router-link to="/dashboard" class="hero-btn secondary">
            View Health Insights
          </router-link>
        </div>
      </div>

      <!-- bottom center arrow -->
      <div class="scroll-arrow" aria-hidden="true">
        <span class="scroll-arrow-text">Scroll to explore</span>
        <span class="scroll-arrow-icon"></span>
      </div>
    </section>

    <section ref="introRef" class="intro-section reveal-section">
      <div class="section-shell">
        <div class="section-heading">
          <p class="section-tag">Why this matters</p>
          <h2>E-waste is not just waste. It is a health and environmental risk.</h2>
          <p class="section-text">
            Old electronics can contain toxic substances such as lead, cadmium, mercury, and
            chromium. If these materials are dumped carelessly, they can harm people and the
            environment over time.
          </p>
        </div>

        <div class="highlight-card">
          <strong>Simple idea</strong>
          <p>
            Most users do not need technical details. They need to know why e-waste matters, what
            risks it creates, and where they can dispose of it safely.
          </p>
        </div>
      </div>
    </section>

    <section ref="featuresRef" class="features-section reveal-section">
      <div class="section-shell">
        <div class="section-heading compact">
          <p class="section-tag">What you can do here</p>
          <h2>Three simple actions</h2>
        </div>

        <div class="feature-grid">
          <router-link to="/dashboard" class="feature-card">
            <div class="feature-top">
              <span class="feature-icon">📊</span>
              <span class="feature-label">Health Insights</span>
            </div>
            <h3>Understand the health impact</h3>
            <p>
              View simple charts that explain why toxic exposure and unsafe disposal should be taken
              seriously.
            </p>
          </router-link>

          <router-link to="/disposal-locations" class="feature-card">
            <div class="feature-top">
              <span class="feature-icon">📍</span>
              <span class="feature-label">Disposal Search</span>
            </div>
            <h3>Find safe disposal locations</h3>
            <p>
              Search for nearby places where you can responsibly take devices, electronics, and
              related waste.
            </p>
          </router-link>

          <div class="feature-card static-card">
            <div class="feature-top">
              <span class="feature-icon">♻️</span>
              <span class="feature-label">Awareness</span>
            </div>
            <h3>Make better e-waste decisions</h3>
            <p>
              Learn why repair, reuse, recycling, and proper disposal are better than throwing old
              devices away.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section ref="journeyRef" class="journey-section reveal-section">
      <div class="section-shell journey-shell">
        <div class="journey-copy">
          <p class="section-tag">User journey</p>
          <h2>From awareness to action</h2>
          <p class="section-text">
            The goal of EcoTech is simple. First, help users understand why e-waste is dangerous.
            Then show the health context clearly. Finally, guide them to the next practical step:
            safe disposal.
          </p>
        </div>

        <div class="journey-steps">
          <div class="step-card">
            <span class="step-number">01</span>
            <h3>Learn</h3>
            <p>Understand why toxic materials in e-waste matter.</p>
          </div>

          <div class="step-card">
            <span class="step-number">02</span>
            <h3>Explore</h3>
            <p>See health-related insights in a simple visual format.</p>
          </div>

          <div class="step-card">
            <span class="step-number">03</span>
            <h3>Act</h3>
            <p>Find a safe place to dispose of your device responsibly.</p>
          </div>
        </div>
      </div>
    </section>

    <section ref="ctaRef" class="cta-section reveal-section">
      <div class="cta-card">
        <p class="section-tag">Take the next step</p>
        <h2>Do not let old electronics become harmful waste.</h2>
        <p>
          Explore disposal locations and make safer choices for your device, your health, and your
          environment.
        </p>
        <router-link to="/disposal-locations" class="hero-btn primary cta-btn">
          Start with Disposal Locations
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import heroImg from '@/assets/e-waste.png'

const introRef = ref(null)
const featuresRef = ref(null)
const journeyRef = ref(null)
const ctaRef = ref(null)

const scrollY = ref(0)
let observer = null

const heroImageStyle = computed(() => {
  const y = Math.min(scrollY.value * 0.12, 80)
  return {
    transform: `translate3d(0, ${y}px, 0)`,
  }
})

const heroContentStyle = computed(() => {
  const y = Math.min(scrollY.value * 0.08, 40)
  const opacity = Math.max(0, 1 - scrollY.value / 850)
  return {
    transform: `translate3d(0, ${y}px, 0)`,
    opacity,
  }
})

function handleScroll() {
  scrollY.value = window.scrollY || 0
}

function setupRevealAnimations() {
  const sections = [introRef.value, featuresRef.value, journeyRef.value, ctaRef.value].filter(
    Boolean,
  )

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed')
          observer?.unobserve(entry.target)
        }
      })
    },
    {
      threshold: 0.14,
      rootMargin: '0px 0px -40px 0px',
    },
  )

  sections.forEach((section) => observer.observe(section))
}

onMounted(() => {
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive: true })
  setupRevealAnimations()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  observer?.disconnect()
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background:
    radial-gradient(circle at 88% 8%, rgba(129, 199, 132, 0.12), transparent 18%),
    radial-gradient(circle at 12% 92%, rgba(67, 160, 71, 0.08), transparent 22%),
    linear-gradient(180deg, #f8fbf8 0%, #eef4ef 100%);
  color: #173a29;
  overflow-x: hidden;
}

.hero {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.hero-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 108%;
  object-fit: cover;
  will-change: transform;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(6, 18, 12, 0.28) 0%,
    rgba(6, 18, 12, 0.42) 55%,
    rgba(6, 18, 12, 0.6) 100%
  );
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 25%, rgba(129, 199, 132, 0.18), transparent 24%),
    radial-gradient(circle at 80% 20%, rgba(67, 160, 71, 0.14), transparent 26%);
  mix-blend-mode: screen;
}

.hero-content {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 7vw;
  color: #ffffff;
  will-change: transform, opacity;
}

.hero-tag {
  display: inline-flex;
  width: fit-content;
  margin: 0 0 18px;
  padding: 9px 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.hero-content h1 {
  margin: 0;
  max-width: 900px;
  font-size: 76px;
  line-height: 0.98;
  font-weight: 800;
  letter-spacing: -2px;
}

.hero-subtitle {
  margin: 22px 0 0;
  max-width: 720px;
  font-size: 20px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 28px;
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  padding: 0 22px;
  border-radius: 999px;
  text-decoration: none;
  font-size: 15px;
  font-weight: 700;
  transition:
    transform 0.28s ease,
    box-shadow 0.28s ease,
    background 0.28s ease,
    border-color 0.28s ease;
}

.hero-btn:hover {
  transform: translateY(-3px);
}

.hero-btn.primary {
  background: #ffffff;
  color: #173a29;
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
}

.hero-btn.primary:hover {
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.22);
}

.hero-btn.secondary {
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.08);
}

.hero-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.14);
}

.scroll-arrow {
  position: absolute;
  left: 50%;
  bottom: 100px;
  transform: translateX(-50%);
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  animation: arrowFloat 1.8s ease-in-out infinite;
}

.scroll-arrow-text {
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.4px;
  color: rgba(255, 255, 255, 0.88);
  text-transform: uppercase;
}

.scroll-arrow-icon {
  width: 16px;
  height: 16px;
  border-right: 3px solid rgba(255, 255, 255, 0.95);
  border-bottom: 3px solid rgba(255, 255, 255, 0.95);
  transform: rotate(45deg);
  display: block;
}

@keyframes arrowFloat {
  0%,
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 0.75;
  }
  50% {
    transform: translateX(-50%) translateY(8px);
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .scroll-arrow {
    bottom: 42px;
    gap: 8px;
  }

  .scroll-arrow-text {
    font-size: 12px;
  }

  .scroll-arrow-icon {
    width: 14px;
    height: 14px;
  }
}

@keyframes arrowFloat {
  0%,
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 0.75;
  }
  50% {
    transform: translateX(-50%) translateY(8px);
    opacity: 1;
  }
}

.section-shell,
.cta-card {
  width: min(1220px, calc(100% - 48px));
  margin: 0 auto;
}

.intro-section,
.features-section,
.journey-section,
.cta-section {
  padding: 84px 0;
}

.reveal-section {
  opacity: 0;
  transform: translateY(48px);
  transition:
    opacity 0.8s ease,
    transform 0.8s ease;
}

.reveal-section.revealed {
  opacity: 1;
  transform: translateY(0);
}

.section-heading {
  max-width: 860px;
}

.section-heading.compact {
  margin-bottom: 28px;
}

.section-tag {
  display: inline-flex;
  margin: 0 0 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(232, 245, 233, 0.9);
  border: 1px solid rgba(207, 232, 209, 0.98);
  color: #2e7d32;
  font-size: 13px;
  font-weight: 700;
}

.section-heading h2,
.cta-card h2 {
  margin: 0;
  font-size: 46px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -1px;
  color: #143324;
}

.section-text,
.cta-card p {
  margin: 18px 0 0;
  font-size: 18px;
  line-height: 1.85;
  color: #557260;
}

.highlight-card {
  margin-top: 28px;
  padding: 26px 28px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(251, 253, 251, 0.96) 100%);
  border: 1px solid rgba(226, 238, 227, 0.98);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.highlight-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 20px;
  color: #173a29;
}

.highlight-card p {
  margin: 0;
  font-size: 16px;
  line-height: 1.8;
  color: #557260;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(260px, 1fr));
  gap: 22px;
}

.feature-card {
  display: block;
  text-decoration: none;
  color: inherit;
  padding: 28px;
  border-radius: 30px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(251, 253, 251, 0.96) 100%);
  border: 1px solid rgba(226, 238, 227, 0.98);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
  transition:
    transform 0.34s ease,
    box-shadow 0.34s ease,
    border-color 0.34s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: rgba(129, 199, 132, 0.58);
  box-shadow:
    0 24px 42px rgba(27, 67, 50, 0.08),
    0 0 0 1px rgba(129, 199, 132, 0.14);
}

.feature-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.feature-icon {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(180deg, #eff8f0 0%, #e7f4e8 100%);
  font-size: 21px;
}

.feature-label {
  font-size: 13px;
  font-weight: 700;
  color: #3f8f46;
}

.feature-card h3 {
  margin: 0 0 12px;
  font-size: 28px;
  line-height: 1.15;
  color: #173a29;
  letter-spacing: -0.5px;
}

.feature-card p {
  margin: 0;
  font-size: 16px;
  line-height: 1.8;
  color: #557260;
}

.static-card {
  cursor: default;
}

.journey-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.95fr);
  gap: 28px;
  align-items: start;
}

.journey-steps {
  display: grid;
  gap: 16px;
}

.step-card {
  padding: 22px 24px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(251, 253, 251, 0.96) 100%);
  border: 1px solid rgba(226, 238, 227, 0.98);
  box-shadow:
    0 18px 34px rgba(27, 67, 50, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.74);
}

.step-number {
  display: inline-block;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 800;
  color: #3f8f46;
}

.step-card h3 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #173a29;
}

.step-card p {
  margin: 0;
  font-size: 15px;
  line-height: 1.75;
  color: #557260;
}

.cta-card {
  padding: 40px;
  border-radius: 34px;
  background: linear-gradient(180deg, rgba(241, 248, 242, 0.92) 0%, rgba(234, 244, 236, 0.92) 100%);
  border: 1px solid rgba(210, 232, 214, 0.98);
  box-shadow:
    0 22px 42px rgba(27, 67, 50, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
}

.cta-btn {
  margin-top: 24px;
  width: fit-content;
}

@media (max-width: 1200px) {
  .feature-grid,
  .journey-shell {
    grid-template-columns: 1fr;
  }

  .hero-content h1 {
    font-size: 62px;
  }
}

@media (max-width: 900px) {
  .hero-content {
    padding: 0 22px;
  }

  .hero-content h1 {
    font-size: 48px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .section-heading h2,
  .cta-card h2 {
    font-size: 36px;
  }
}

@media (max-width: 640px) {
  .hero-content h1 {
    font-size: 38px;
    line-height: 1.05;
  }

  .hero-subtitle {
    font-size: 16px;
    line-height: 1.75;
  }

  .hero-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-shell,
  .cta-card {
    width: min(100% - 24px, 1220px);
  }

  .intro-section,
  .features-section,
  .journey-section,
  .cta-section {
    padding: 64px 0;
  }

  .section-heading h2,
  .cta-card h2 {
    font-size: 30px;
  }

  .feature-card h3 {
    font-size: 24px;
  }

  .cta-card {
    padding: 28px 22px;
  }

  .scroll-arrow {
    bottom: 24px;
  }
}
</style>
