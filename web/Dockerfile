##### DEPENDENCIES

FROM cnharbor.amway.com.cn/lightai/node:20-alpine AS deps
RUN apk add --no-cache libc6-compat openssl
WORKDIR /app


# Install dependencies based on the preferred package manager

COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml ./

RUN npm install .

##### BUILDER

FROM cnharbor.amway.com.cn/lightai/node:20-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

##### RUNNER

FROM cnharbor.amway.com.cn/lightai/node:20-debian12 AS runner
WORKDIR /app

ENV NODE_ENV=production

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000

CMD ["server.js"]
