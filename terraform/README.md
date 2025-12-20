# Infrastructure Configuration

This directory contains Terraform configuration for deploying the Household Management Application.

## Cloud Provider Options

### Option 1: Railway.app (Recommended for Free Tier)
Railway provides a simpler deployment experience with a generous free tier:
- $5/month free credit
- PostgreSQL database included
- Automatic HTTPS
- Simple deployment from Git

**Setup Steps:**
1. Create account at railway.app
2. Create new project
3. Add PostgreSQL service
4. Add web service (connect to GitHub repo)
5. Set environment variables
6. Deploy

**No Terraform needed** - Railway manages infrastructure through their UI/CLI.

### Option 2: Render.com
Similar to Railway:
- Free tier available (with limitations)
- PostgreSQL free tier
- Simple deployment

**Setup Steps:**
1. Create account at render.com
2. Create PostgreSQL database
3. Create web service
4. Connect GitHub repo
5. Configure environment variables

### Option 3: AWS (More Complex, More Control)
Use the Terraform configuration in this directory for AWS deployment.

**Prerequisites:**
- AWS account
- AWS CLI configured
- Terraform installed

**Setup Steps:**
1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill in your values (especially `db_password`)
3. Initialize Terraform: `terraform init`
4. Review plan: `terraform plan`
5. Apply: `terraform apply`

**AWS Free Tier:**
- 750 hours/month of t2.micro/t3.micro instances
- 20GB storage for RDS
- 5GB S3 storage
- Valid for 12 months

## Required Infrastructure Components

Regardless of provider, you need:

1. **PostgreSQL Database**
   - Version: 14+ recommended
   - Storage: 20GB minimum (free tier)
   - Backups: Daily backups recommended

2. **Application Hosting**
   - Container service (Railway, Render, ECS, etc.)
   - Or serverless (AWS Lambda, etc.)
   - Minimum: 512MB RAM, 1 vCPU

3. **Email Service**
   - SendGrid (free: 100 emails/day)
   - AWS SES (free: 62,000 emails/month)
   - Or SMTP server

4. **Environment Variables**
   - `DATABASE_URL` - PostgreSQL connection string
   - `SECRET_KEY` - JWT secret key
   - `EMAIL_API_KEY` - Email service API key
   - `EMAIL_FROM` - Sender email address
   - `FRONTEND_URL` - Frontend application URL

## Security Considerations

1. **Database Access**
   - Use private networking when possible
   - Restrict access to application only
   - Use strong passwords
   - Enable SSL/TLS connections

2. **Secrets Management**
   - Never commit secrets to Git
   - Use environment variables
   - Consider AWS Secrets Manager for production

3. **Network Security**
   - Use security groups/firewalls
   - Restrict database to application only
   - Enable HTTPS for all traffic

4. **Backups**
   - Enable automated database backups
   - Test restore procedures
   - Store backups securely

## Cost Estimation (Free Tier)

### Railway.app
- Free tier: $5/month credit
- PostgreSQL: ~$5/month (covered by credit)
- Web service: ~$5/month (covered by credit)
- **Total: Free for small usage**

### Render.com
- PostgreSQL: Free tier available
- Web service: Free tier (spins down after inactivity)
- **Total: Free with limitations**

### AWS
- RDS: Free tier (12 months)
- EC2/ECS: Free tier (12 months)
- **Total: Free for 12 months, then ~$15-30/month**

## Deployment Checklist

- [ ] Database instance created and accessible
- [ ] Application deployed and running
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] HTTPS/SSL configured
- [ ] Email service configured and tested
- [ ] Monitoring/logging set up
- [ ] Backups configured
- [ ] Domain name configured (optional)
- [ ] Security groups/firewalls configured

## Troubleshooting

### Database Connection Issues
- Verify security group allows connections
- Check database endpoint/URL
- Verify credentials
- Test connection from application host

### Application Deployment Issues
- Check environment variables
- Verify Docker image builds correctly
- Check application logs
- Verify port configuration

### Email Issues
- Verify API keys
- Check email service quotas
- Verify sender email is verified
- Check spam folders

