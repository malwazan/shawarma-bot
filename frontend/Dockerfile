FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build && npm prune --omit=dev


FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production

# The server bundle imports react, @tanstack/* etc. at runtime, so it needs
# the production node_modules alongside the build output.
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

EXPOSE 3000
CMD ["npm", "start"]
