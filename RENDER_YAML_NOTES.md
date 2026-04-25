# Render.yaml Configuration Notes

## Important Changes Made

### ✅ Fixed Structure
The `render.yaml` file has been updated to use the correct Render Blueprint format:

1. **Databases Section**: PostgreSQL is now defined in the top-level `databases` section (not as a service)
2. **No Docker**: All services use native runtimes (`python`, `node`, `redis`) - no Docker containers
3. **Root Directory**: Each service uses `rootDir` to specify its working directory instead of `cd` commands
4. **Simplified Commands**: Build and start commands are simplified without shell scripts

## Correct Structure

```yaml
databases:
  - name: escrow-postgres
    databaseName: escrow_db
    user: escrow_user
    plan: starter

services:
  - type: redis
    name: escrow-redis
    ...
  
  - type: web
    name: escrow-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt && python manage.py migrate
    startCommand: daphne -b 0.0.0.0 -p $PORT config.asgi:application
    ...
```

## Key Points

### 1. Database Configuration
- ✅ Use `databases` section at the top level
- ✅ Reference with `fromDatabase` in service envVars
- ❌ Don't use `type: pserv` or nested `databases` field

### 2. Service Types
- **Web Services**: `type: web` with `runtime: python` or `runtime: node`
- **Workers**: `type: worker` with `runtime: python`
- **Redis**: `type: redis` (managed service)
- **PostgreSQL**: Defined in `databases` section

### 3. Working Directory
- ✅ Use `rootDir: backend` or `rootDir: frontend`
- ✅ Commands run relative to rootDir
- ❌ Don't use `cd backend &&` in commands

### 4. Runtime vs Environment
- ✅ Use `runtime: python` or `runtime: node`
- ❌ Don't use `env: python` or `env: docker`

## Environment Variable Linking

### From Database
```yaml
- key: DATABASE_URL
  fromDatabase:
    name: escrow-postgres
    property: connectionString
```

### From Service
```yaml
- key: REDIS_URL
  fromService:
    type: redis
    name: escrow-redis
    property: connectionString
```

### From Another Service's EnvVar
```yaml
- key: SECRET_KEY
  fromService:
    type: web
    name: escrow-backend
    envVarKey: SECRET_KEY
```

## Common Errors Fixed

### ❌ Error: "field databases not found"
**Cause**: Using `databases` field under a service definition
**Fix**: Move database to top-level `databases` section

### ❌ Error: "unknown field env"
**Cause**: Using `env: python` instead of `runtime: python`
**Fix**: Use `runtime` field with correct value

### ❌ Error: "unknown field type pserv"
**Cause**: Trying to use Docker-style service type
**Fix**: Use native `databases` section for PostgreSQL

## Validation

To validate your `render.yaml`:
1. Push to GitHub
2. Create Blueprint in Render
3. Render will validate the file
4. Fix any errors shown in the UI

## References

- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Render Databases](https://render.com/docs/databases)
- [Render Environment Variables](https://render.com/docs/environment-variables)
