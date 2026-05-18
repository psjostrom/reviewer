# Springa: React & Next.js Patterns

Check for: unnecessary `'use client'` directives (should be pushed as far down the tree as possible), missing `await` on async request APIs (`cookies()`, `headers()`, `params`, `searchParams` — all async in Next.js 16), stale closures in hooks, missing dependency arrays, server actions used correctly (`'use server'`), proper error boundaries, components that should be server components but aren't.

**Scope boundaries:** Loading/error/undefined state handling belongs to the **Error & Edge Cases** agent — don't duplicate their work. Only return actual problems — no positive observations.
