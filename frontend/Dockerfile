FROM node:20-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy source code
COPY frontend .

# Expose Vite dev server port
EXPOSE 5173

# Start Vite dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
