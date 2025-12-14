# Frontend Dockerfile for Money Map Manager
# Uses multi-stage build with Bun for fast builds.

# ============================================
# Stage 1: Dependencies
# ============================================
FROM oven/bun:1-slim AS deps

WORKDIR /app

# Copy dependency files.
COPY package.json bun.lock* ./

# Install dependencies.
RUN bun install --frozen-lockfile

# ============================================
# Stage 2: Build
# ============================================
FROM oven/bun:1-slim AS builder

WORKDIR /app

# Copy dependencies from deps stage.
COPY --from=deps /app/node_modules ./node_modules

# Copy source code.
COPY . .

# Build argument for API URL (set at build time).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application.
RUN bun run build

# ============================================
# Stage 3: Production
# ============================================
FROM oven/bun:1-slim AS production

WORKDIR /app

# Create non-root user for security.
RUN groupadd --gid 1001 nodejs && \
    useradd --uid 1001 --gid nodejs --shell /bin/bash --create-home nextjs

# Copy built application.
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user.
USER nextjs

# Expose port.
EXPOSE 3000

# Set environment variables.
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check using bun (no external tools needed).
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD bun --eval "fetch('http://localhost:3000').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

# Run the application.
CMD ["bun", "server.js"]
