# RDS + S3 Setup

## 1. Create S3 Bucket

Go to **S3 → Create bucket**

- Bucket name: `silicon-plate-data`
- Region: `ap-south-1` (Mumbai) or wherever you are
- Block all public access: ON
- Everything else: defaults

## 2. Launch RDS PostgreSQL

Go to **RDS → Create database**

- Engine: PostgreSQL
- Template: **Free tier**
- DB instance identifier: `silicon-plate-db`
- Master username: `postgres`
- Master password: (set something, you'll put it in .env)
- Instance type: `db.t3.micro`
- Storage: 20 GB gp2 (default)
- Public access: **Yes** (so you can connect from your machine)
- VPC security group: create new, or use default — add an inbound rule for port `5432` from your IP

After it launches (~5 mins), grab the **Endpoint** from the RDS console. Looks like:

```
silicon-plate-db.xxxxxxxxxx.ap-south-1.rds.amazonaws.com
```

## 3. Create the database

Connect via psql and create the DB:

```bash
psql -h <your-endpoint> -U postgres -p 5432
```

```sql
CREATE DATABASE zomatodb;
\q
```

Then run the schema:

```bash
psql -h <your-endpoint> -U postgres -d zomatodb -f sql/01_create_schema.sql
```

## 4. AWS credentials

Make sure `aws configure` is done (needed for S3 upload):

```bash
aws configure
# AWS Access Key ID: ...
# AWS Secret Access Key: ...
# Default region: ap-south-1
# Default output format: json
```

Or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as env vars.

## 5. Fill in .env

```env
AWS_S3_BUCKET=silicon-plate-data

RDS_HOST=silicon-plate-db.xxxxxxxxxx.ap-south-1.rds.amazonaws.com
RDS_PORT=5432
RDS_DBNAME=zomatodb
RDS_USER=postgres
RDS_PASSWORD=your-password-here
```

## 6. Run the load

```bash
uv run python etl/03_load.py
```

Should print row counts for each table. Verify in psql:

```sql
SELECT COUNT(*) FROM fact_restaurant_performance;
-- expect ~51717
```
