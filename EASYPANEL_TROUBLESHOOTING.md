# Easypanel Deployment Troubleshooting Guide

## Current Issue: PostgreSQL Container Unhealthy

### What Happened

When deploying to Easypanel, you got this error:
```
Container saas-motos_motogestor-postgres-1  Error
dependency failed to start: container saas-motos_motogestor-postgres-1 is unhealthy
```

### Root Cause

The PostgreSQL health check was failing because:
1. **Environment variable substitution doesn't work in health checks** - The health check used `${POSTGRES_USER}` which Docker couldn't resolve inside the container
2. **Timing issues** - PostgreSQL might need more time to initialize, especially on first run
3. **No start_period** - The health check started immediately without giving PostgreSQL time to start

### What I Fixed

I updated the PostgreSQL health check in all docker-compose files:

**Before (broken):**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-motogestor} -d ${POSTGRES_DB:-motogestor_prod}"]
  interval: 10s
  timeout: 5s
  retries: 10
```

**After (fixed):**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready"]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 30s  # NEW: Gives PostgreSQL 30 seconds to initialize
```

**Why this works:**
- `pg_isready` without parameters checks if PostgreSQL is ready (default postgres user)
- `start_period: 30s` gives PostgreSQL 30 seconds before health checks count as failures
- Simpler = more reliable

---

## Step-by-Step: Deploy to Easypanel (After Fix)

### 1. Pull the Latest Changes

Make sure you have the latest fixes:

```bash
cd /home/user/motogestor-v2
git pull origin claude/debug-api-gateway-frontend-dubeC
```

### 2. Commit and Push (If Testing This Fix)

```bash
git add -A
git commit -m "Fix PostgreSQL health check for Easypanel deployment"
git push origin claude/debug-api-gateway-frontend-dubeC
```

### 3. In Easypanel Dashboard

#### A. Update Your Project

1. Go to your MotoGestor project in Easypanel
2. Click on **Settings** or **Configuration**
3. Make sure it's pulling from the correct branch: `claude/debug-api-gateway-frontend-dubeC`
4. Click **Deploy** or **Redeploy**

#### B. Check Environment Variables

Make sure these are set in Easypanel:

**Required:**
```bash
POSTGRES_USER=motogestor
POSTGRES_PASSWORD=<your-secure-password-here>
POSTGRES_DB=motogestor_prod
DATABASE_URL=postgresql://motogestor:<your-password>@postgres:5432/motogestor_prod
JWT_SECRET_KEY=<your-secret-key-here>
```

**Optional (if using AI service):**
```bash
OPENAI_API_KEY=<your-openai-key>
```

**Important:** Replace `<your-secure-password-here>` with an actual secure password!

### 4. Watch the Deployment

In Easypanel, you should see:
1. PostgreSQL starting
2. PostgreSQL becoming healthy (after ~30 seconds)
3. Other services starting (users-service, management-service, etc.)
4. API gateway becoming healthy

### 5. If PostgreSQL Still Fails

If PostgreSQL still shows as unhealthy, try these debugging steps:

#### Option A: Check PostgreSQL Logs in Easypanel

1. In Easypanel, go to your project
2. Click on **Logs**
3. Filter for the `postgres` container
4. Look for error messages like:
   - `FATAL: password authentication failed`
   - `permission denied`
   - `data directory not empty`

#### Option B: Clear the Volume (Fresh Start)

**WARNING: This deletes all data!**

If you suspect corrupted data or old migrations:

1. In Easypanel, go to **Volumes**
2. Delete the `pgdata-prod` volume
3. Redeploy the project
4. This forces PostgreSQL to start fresh

#### Option C: Check Volume Permissions

Some hosting platforms have permission issues with volumes:

1. SSH into your Easypanel server (if you have access)
2. Run:
   ```bash
   docker exec -it saas-motos_motogestor-postgres-1 ls -la /var/lib/postgresql/data
   ```
3. Check if the postgres user owns the directory

### 6. After PostgreSQL is Healthy: Run Migrations

**CRITICAL:** You must run migrations before the app will work!

#### In Easypanel Console:

1. Open **Console** for the `users-service` container
2. Run:
   ```bash
   alembic upgrade head
   ```

3. Repeat for each service:
   - `management-service`
   - `financial-service`
   - `teamcrm-service`

#### Or via SSH (if you have server access):

```bash
# Find the container names
docker ps | grep motogestor

# Run migrations
docker exec -it saas-motos_motogestor-users-service-1 alembic upgrade head
docker exec -it saas-motos_motogestor-management-service-1 alembic upgrade head
docker exec -it saas-motos_motogestor-financial-service-1 alembic upgrade head
docker exec -it saas-motos_motogestor-teamcrm-service-1 alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 20240904115900, Initial schema for users-service
INFO  [alembic.runtime.migration] Running upgrade 20240904115900 -> 20240909130000, Add RLS policies and token revocation table
```

### 7. Verify Deployment

After everything is running:

```bash
# Check API Gateway health
curl https://your-domain.com/health

# Expected: {"status": "healthy"}
```

Open your browser and visit `https://your-domain.com`

---

## Common Easypanel Issues & Solutions

### Issue 1: "Build failed - frontend/dist not found"

**Problem:** The api-gateway Docker build can't find `frontend/dist/`

**Solution:** Easypanel needs to build the frontend before building the api-gateway image.

**Fix:** Add a build script in Easypanel:
1. Go to **Build Settings**
2. Add **Pre-build command:**
   ```bash
   cd frontend && npm ci && npm run build && cd ..
   ```

### Issue 2: "Port 80 already in use"

**Problem:** Another service is using port 80

**Solutions:**
- Change the port in `docker-compose.yml`: `ports: - "8080:5000"`
- Or stop the conflicting service
- Or use Easypanel's reverse proxy instead

### Issue 3: "Cannot connect to database"

**Problem:** Services can't connect to PostgreSQL

**Check:**
1. Is PostgreSQL healthy? Check logs
2. Is `DATABASE_URL` set correctly?
   - Format: `postgresql://USER:PASSWORD@postgres:5432/DATABASE`
   - Use `postgres` as hostname (Docker service name)
3. Are environment variables set in Easypanel?

### Issue 4: "Migration failed: already exists"

**Problem:** Tables already exist from a previous deployment

**Solutions:**

**Option A (Safe):** Check current migration state:
```bash
docker exec -it <container> alembic current
```

**Option B (Fresh start - DELETES DATA):**
1. Delete the `pgdata-prod` volume in Easypanel
2. Redeploy
3. Run migrations again

### Issue 5: "CORS errors in frontend"

**Problem:** Browser blocks API calls due to CORS

**Check:** Make sure the frontend is served from the same domain as the API (both through api-gateway)

**If running frontend separately:**
Update CORS in `api-gateway/app/__init__.py`:
```python
CORS(app, resources={r"/*": {"origins": ["https://your-frontend-domain.com"]}})
```

---

## Easypanel Best Practices

### 1. Use Environment Variables

Never hardcode secrets in docker-compose files. Always use environment variables in Easypanel:

- Database passwords
- JWT secrets
- API keys

### 2. Use Pre-built Images (Recommended)

Instead of building on Easypanel (slow), use GitHub Actions to build and push to GHCR:

1. Set up `CR_PAT` secret in GitHub
2. Tag a release: `git tag v1.0.0 && git push origin v1.0.0`
3. GitHub Actions builds and publishes images
4. Use `docker-compose.easypanel-prod.yml` which uses GHCR images

### 3. Monitor Logs

Always check logs when debugging:
- Easypanel Dashboard → Logs
- Filter by service name
- Look for errors in order: postgres → users-service → api-gateway

### 4. Health Checks

All services have health checks. If a service is unhealthy:
1. Check its logs
2. Check its dependencies (database, other services)
3. Verify environment variables

---

## Quick Reference: Useful Commands

### Check Container Status
```bash
docker ps
docker ps -a  # Shows stopped containers
```

### View Logs
```bash
docker logs saas-motos_motogestor-postgres-1
docker logs -f saas-motos_motogestor-api-gateway-1  # Follow logs
```

### Execute Commands in Container
```bash
docker exec -it saas-motos_motogestor-postgres-1 bash
docker exec -it saas-motos_motogestor-users-service-1 alembic current
```

### Check Database
```bash
docker exec -it saas-motos_motogestor-postgres-1 psql -U motogestor -d motogestor_prod
```

Inside psql:
```sql
\dt  -- List tables
\d users  -- Describe users table
SELECT * FROM alembic_version;  -- Check migration version
```

### Restart Service
```bash
docker restart saas-motos_motogestor-api-gateway-1
```

### Check Health
```bash
docker inspect saas-motos_motogestor-postgres-1 | grep -A 10 Health
```

---

## Emergency Recovery

If everything is broken and you need a fresh start:

### Nuclear Option (Deletes All Data)

1. In Easypanel:
   - Stop the project
   - Delete all volumes
   - Delete all containers

2. Redeploy from scratch:
   - Pull latest code
   - Set environment variables
   - Deploy
   - Run migrations

3. Seed initial data:
   ```bash
   docker exec -it saas-motos_motogestor-users-service-1 python -c "
   from app.seed import seed_demo_user
   seed_demo_user()
   "
   ```

---

## Getting Help

When asking for help, provide:

1. **Error message** (full output)
2. **Logs** from the failing container
3. **Docker compose file** you're using
4. **Environment variables** (without showing secrets)
5. **Steps you tried**

Example:
```
Error: Container postgres unhealthy
Logs show: FATAL: password authentication failed
Using: docker-compose.yml
Env vars set: POSTGRES_USER, POSTGRES_DB (but forgot POSTGRES_PASSWORD!)
Tried: Redeploying 3 times
```

---

## Summary of This Fix

**Files changed:**
- `docker-compose.yml` - Simplified PostgreSQL health check
- `docker-compose.prod.yml` - Simplified PostgreSQL health check
- `docker-compose.easypanel-prod.yml` - Simplified PostgreSQL health check
- `docker-compose.dev.yml` - Simplified PostgreSQL health check

**What changed:**
- Removed environment variable substitution from health check
- Added `start_period: 30s` to give PostgreSQL time to initialize
- Increased retries to 10 for production files

**Next steps:**
1. Pull these changes
2. Push to your repository
3. Redeploy in Easypanel
4. PostgreSQL should now become healthy
5. Run migrations
6. Test the application

Good luck! 🚀
