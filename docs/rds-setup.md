# RDS + S3 Setup

## 1. Create S3 Bucket

Go to **S3 → Create bucket**

- Bucket name: `silicon-plate-data`
- Region: `ap-south-1` (Mumbai) or wherever you are
- Block all public access: ON
- Everything else: defaults

## 2. Launch RDS PostgreSQL

Go to **RDS → Create database**

> ⚠️ Make sure you pick **PostgreSQL**, NOT Aurora. Aurora costs ~$2000/month. Plain RDS PostgreSQL has a free tier.

Settings to use:

| Field | Value |
|---|---|
| Engine | PostgreSQL |
| Template | **Free tier** |
| DB instance identifier | `silicon-plate-db` |
| Master username | `postgres` |
| Credentials management | Self managed |
| Master password | (your choice) |
| Instance type | `db.t3.micro` (auto-set by free tier) |
| Storage | 20 GB gp2 |
| Public access | **Yes** |
| VPC security group | Create new → name it `silicon-plate-sg` |
| Initial database name | `zomatodb` ← set this under **Additional configuration** |

The "Initial database name" field saves you from having to create it manually.

After it launches (~5 mins), grab the **Endpoint** from the RDS console. Looks like:

```
silicon-plate-db.xxxxxxxxxx.ap-south-1.rds.amazonaws.com
```

Then allow your IP on port 5432:
- Go to the security group → Inbound rules → Add rule
- Type: PostgreSQL, Port: 5432, Source: My IP

## 3. Run the schema

No need to create the database manually (done via "Initial database name" above). Just run:

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
