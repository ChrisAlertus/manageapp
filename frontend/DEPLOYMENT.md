# Railway.app Deployment


# Create a Service from a Github Repo

Choose the repository that has the frontend code and specify the specific branch of interest as well as the subfolder for the backend files `frontend/`.

For Frontend (separate service):
1.  Create another service in the same Railway project
2. Point to /frontend directory
3. Set build command: npm install && npm run build
4. Set start command: You'll need a simple server (see below)

Frontend Service Variables:
```bash
VITE_API_URL=<your-backend-railway-url>
```

Healthcheck path
```bash
<your-backend-railway-url>/health
```
Build Command:
```bash
npm install && npm run build
```
Start command
```bash
npx serve -s dist -l $PORT
```

To get a publicly accessible domain, check under the frontend "Networking" and click "Public Domain" (I think). It will generate a url which you can use to access the running app from your browser. It lives!

Quick pause checklist
[ ] Pause frontend service
[ ] Pause backend service
[ ] Export PostgreSQL data (optional)
[ ] Pause or delete PostgreSQL service
[ ] Verify no active deployments