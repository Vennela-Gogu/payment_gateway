# Use Node LTS
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files first (for caching)
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose frontend port
EXPOSE 3000

# Build the app
RUN npm run build

# Install serve to run built app
RUN npm install -g serve

# Start the checkout app
CMD ["serve", "-s", "dist", "-l", "3000"]