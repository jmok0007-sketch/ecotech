<script setup>
const links = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/disposal-locations', label: 'Disposal' },
  { to: '/repair-check', label: 'Repair' },
  { to: '/extend-usage', label: 'Extend Usage' },
  { to: '/ai-chat', label: 'AI Chat' },
  { to: '/safe-guidance', label: 'Safe Guidance' },
]
</script>

<template>
  <nav class="nav">
    <div class="nav-brand">
      <router-link to="/">EcoTech</router-link>
    </div>
    <ul class="nav-links">
      <li v-for="l in links" :key="l.to">
        <router-link :to="l.to">{{ l.label }}</router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.nav-brand a {
  font-weight: 700;
  font-size: 1.2rem;
  color: var(--color-primary);
}
.nav-links {
  list-style: none;
  display: flex;
  gap: 1rem;
  margin: 0;
  padding: 0;
}
.nav-links a {
  color: var(--color-text);
  font-size: 0.95rem;
}
.nav-links a.router-link-active {
  color: var(--color-primary);
  font-weight: 600;
}
</style>
