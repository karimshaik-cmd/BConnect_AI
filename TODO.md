# TODO: Set up Single Production Server (Frontend + Backend)

- [x] Install http-proxy-middleware in frontend
- [x] Modify frontend/server.js to proxy /api/* requests to backend
- [x] Update frontend/src/BankingChat.jsx to use API_BASE_URL = '/api'
- [x] Update frontend/src/components/UserPage.jsx to use API_BASE_URL = '/api'
- [x] Update frontend/package.json with combined run script
- [x] Test the single server setup

# TODO: Set up Vite React app with Node.js HTTP server using Express

- [x] Install Express in frontend folder: Run `npm install express` in frontend/
- [x] Build the app: Run `npm run build` in frontend/ to generate /dist folder
- [x] Create frontend/server.js with Express server code for serving static files and SPA routing
- [x] Update frontend/package.json to add "serve": "node server.js" script
- [x] Test the server: Run `npm run serve` and verify it runs on http://localhost:8080
