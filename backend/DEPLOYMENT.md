# Railway.app Deployment

Firstly, add a Postgres service to the railway project. This does not need any configuration, but once running Railway will create an environment variable that the backend service will use to communicate with the db.

# Create a Service from a Github Repo

Choose the repository that has the backend code and specify the specific branch of interest as well as the subfolder for the backend files `backend/`.

## Required Environment Variables for Railway backend service
Add these in Railway (some may be auto-provided):
Required:
- JWT_SECRET_KEY - Generate a secure random string (you can use: openssl rand -hex 32)
- DATABASE_URL - Railway will auto-provide this if you add a PostgreSQL service
- BACKEND_CORS_ORIGINS - Your frontend URL (see below)
- INVITATION_ACCEPT_URL_BASE - Your frontend URL + /invitations/accept (see below)
- EMAIL_PROVIDER - console / resend
- RESEND_API_KEY - if using resend email service, then include the API key here

Note: the frontend URL can be found in the frontend service box under "Networking".