# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
RUN mkdir -p result_build && cp -r build/* result_build/
CMD ["sh", "-c", "echo Frontend image ready"]
#  CMD cp -r build result_build
