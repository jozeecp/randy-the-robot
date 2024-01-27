FROM node:21-alpine

# Create app directory
WORKDIR /app

# Install app dependencies
COPY . .
RUN npm ci

# Build app
RUN npm run build

# Expose port
EXPOSE 9000

# Start app
CMD [ "npm", "start" ]
