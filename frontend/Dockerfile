FROM node:18-alpine

WORKDIR /app

# Copy package files first
COPY package.json package-lock.json* ./
RUN npm install

# Copy rest of the project (including index.html)
COPY . .

# Build the app
RUN npm run build

# Install serve to run built app
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]