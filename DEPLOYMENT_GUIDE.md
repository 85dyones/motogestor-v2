# MotoGestor v2 - Deployment Guide

## What Was Fixed

I fixed **2 critical bugs** that were causing your database migrations to fail:

1. **Broken Migration Chain** - The migration file had the wrong reference ID
2. **Missing Database Permissions** - The revoked_tokens table wasn't granted proper access

These fixes are now in your branch: `claude/debug-api-gateway-frontend-dubeC`

---

## Step-by-Step Guide: Test Locally

Before deploying to Easypanel, test locally to make sure everything works:

### 1. Pull the Latest Changes

```bash
cd /home/user/motogestor-v2
git pull origin claude/debug-api-gateway-frontend-dubeC
```

### 2. Build the Frontend

The API gateway needs the frontend build artifacts:

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Start the Database

```bash
docker compose -f docker-compose.dev.yml up -d postgres
```

Wait about 10 seconds for PostgreSQL to fully start.

### 4. Run the Migrations

Test each service migration:

```bash
# Users service (this was the broken one)
docker compose -f docker-compose.dev.yml run --rm users-service alembic upgrade head

# Management service
docker compose -f docker-compose.dev.yml run --rm management-service alembic upgrade head

# Financial service
docker compose -f docker-compose.dev.yml run --rm financial-service alembic upgrade head

# TeamCRM service
docker compose -f docker-compose.dev.yml run --rm teamcrm-service alembic upgrade head
```

**Expected Result:** All should complete successfully with no errors.

### 5. Start All Services

```bash
docker compose -f docker-compose.dev.yml up --build
```

### 6. Test the Application

Open your browser and go to:
- **Frontend:** http://localhost:5000
- **API Gateway Health:** http://localhost:5000/health
- **Users Service:** http://localhost:5001/health

### 7. Clean Up (When Done Testing)

```bash
docker compose -f docker-compose.dev.yml down -v
```

The `-v` flag removes volumes, giving you a fresh start next time.

---

## Step-by-Step Guide: Deploy to Easypanel

### Prerequisites

Before deploying, make sure you have:
- Access to your Easypanel dashboard
- Your repository connected to Easypanel
- Environment variables configured in Easypanel

### 1. Merge Your Changes (Optional but Recommended)

If you're ready to deploy, merge your fixes to your main branch:

```bash
git checkout main
git merge claude/debug-api-gateway-frontend-dubeC
git push origin main
```

Or create a Pull Request on GitHub and merge it there.

### 2. Update Easypanel Configuration

In your Easypanel dashboard:

#### A. Update Docker Compose Configuration

1. Go to your MotoGestor v2 project in Easypanel
2. Update the deployment configuration to use `docker-compose.yml` or `docker-compose.prod.yml`
3. Make sure these environment variables are set:

```bash
# Database
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=<your-secure-password>
POSTGRES_DB=motogestor_prod
DATABASE_URL=postgresql://motogestor:<password>@postgres:5432/motogestor_prod

# JWT
JWT_SECRET_KEY=<your-secret-key>

# API Keys (if using)
OPENAI_API_KEY=<your-openai-key>
```

#### B. Ensure Port 80 is Exposed

The API gateway must be accessible on port 80. In your `docker-compose.yml`, verify:

```yaml
api-gateway:
  ports:
    - "80:5000"  # This line is critical!
```

### 3. Build Process in Easypanel

Easypanel needs to:
1. **Build the frontend first** (creates `frontend/dist/`)
2. **Build the api-gateway image** (copies `frontend/dist/` into the image)
3. **Build other services**

#### Option A: Pre-build Script (Recommended)

If Easypanel supports pre-build hooks, add this script:

```bash
#!/bin/bash
cd frontend
npm ci
npm run build
cd ..
```

#### Option B: GitHub Actions (Automated)

The repository already has CI/CD configured. When you push:
1. GitHub Actions builds everything
2. Publishes Docker images to GitHub Container Registry (GHCR)
3. Easypanel pulls the pre-built images

To use this approach:
1. Create a GitHub Personal Access Token with `write:packages` permission
2. Add it to your repository secrets as `CR_PAT`
3. Tag a release: `git tag v1.0.0 && git push origin v1.0.0`
4. Images will be published to: `ghcr.io/85dyones/motogestor-v2-*`
5. Update Easypanel to use these images

### 4. Run Database Migrations in Easypanel

**IMPORTANT:** After deploying, you must run migrations before the app can work.

#### Using Easypanel Console:

1. Open the Easypanel console for your project
2. Access the users-service container
3. Run:

```bash
alembic upgrade head
```

4. Repeat for other services (management, financial, teamcrm)

#### Using Docker Exec (if you have server access):

```bash
# Find container IDs
docker ps | grep motogestor

# Run migrations in each service
docker exec -it <users-service-container-id> alembic upgrade head
docker exec -it <management-service-container-id> alembic upgrade head
docker exec -it <financial-service-container-id> alembic upgrade head
docker exec -it <teamcrm-service-container-id> alembic upgrade head
```

### 5. Verify Deployment

After deploying:

1. **Check API Gateway:**
   ```bash
   curl https://your-domain.com/health
   ```
   Should return: `{"status": "healthy"}`

2. **Check Frontend:**
   Visit `https://your-domain.com` in your browser

3. **Check Database Connection:**
   ```bash
   curl https://your-domain.com/api/health
   ```

4. **Check Logs:**
   In Easypanel, view logs for each service to ensure no errors

### 6. Test User Registration/Login

1. Visit your domain
2. Try to register a new user
3. Try to log in
4. Verify you can access the dashboard

---

## Troubleshooting Common Issues

### Issue: "Migration failed: Revision not found"

**Solution:** Make sure you pulled the latest changes with the migration fix:
```bash
git pull origin claude/debug-api-gateway-frontend-dubeC
```

### Issue: "Error: revoked_tokens: permission denied"

**Solution:** This is fixed by the second bug fix (GRANT statement). Rebuild the database:
```bash
docker compose down -v
docker compose up -d postgres
# Run migrations again
```

### Issue: "Frontend not loading / 404 errors"

**Solution:** Make sure frontend was built before the Docker image:
```bash
cd frontend && npm run build && cd ..
docker compose up --build
```

### Issue: "CORS errors in browser"

**Solution:** Check that CORS is configured in `api-gateway/app/__init__.py`:
```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

### Issue: "Connection refused to services"

**Solution:** Make sure all services are in the same Docker network and using service names (not localhost):
```yaml
USERS_SERVICE_URL: http://users-service:5000  # ✓ Correct
USERS_SERVICE_URL: http://localhost:5000      # ✗ Wrong
```

---

## Database Architecture Note

All services share **one PostgreSQL database** but use **different tables**:

- **users-service:** `tenants`, `users`, `revoked_tokens`
- **management-service:** management tables
- **financial-service:** financial tables
- **teamcrm-service:** CRM tables

Each service runs its own migrations independently.

---

## Quick Reference Commands

```bash
# Test locally
docker compose -f docker-compose.dev.yml up --build

# Run migrations
docker compose run --rm users-service alembic upgrade head

# View logs
docker compose logs -f api-gateway

# Rebuild everything
docker compose down -v
docker compose up --build

# Stop everything
docker compose down

# Check running containers
docker ps
```

---

## Need More Help?

If you encounter issues:

1. **Check the logs:** `docker compose logs -f <service-name>`
2. **Check database:** `docker compose exec postgres psql -U motogestor -d motogestor_prod`
3. **Verify environment variables:** `docker compose config`
4. **Test migrations:** `docker compose run --rm users-service alembic current`

---

## Summary of Changes Made

### Files Changed:
1. `api-gateway/Dockerfile` - Fixed malformed syntax, changed build context
2. `docker-compose.yml` - Added port mapping (80:5000)
3. `docker-compose.dev.yml` - Updated build context for api-gateway
4. `.github/workflows/ci-build-and-test.yml` - Added frontend build step
5. `users-service/migrations/versions/20240909130000_rls_and_revocation.py` - Fixed migration bugs
6. `frontend/.env.example` - Added configuration template

### What Works Now:
✅ Database migrations run successfully
✅ API gateway serves frontend files
✅ API gateway is accessible on port 80
✅ Docker builds include frontend artifacts
✅ CI/CD pipeline builds everything correctly

Good luck with your deployment! 🚀
