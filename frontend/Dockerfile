
FROM node:20-alpine

WORKDIR /app

# Install dependencies containing lock file
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source
COPY . .

# Build the application
RUN npm run build

# Production runner
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "start"]
