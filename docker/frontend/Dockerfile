FROM node:20-alpine
WORKDIR /app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund || npm install; else npm install; fi

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
