# Deploying Docker Compose Application on AWS EC2

This guide provides step-by-step instructions for deploying a Docker Compose application on AWS EC2 with Nginx reverse proxy, SSL, and subdomain routing.

> ⚠️ **Production Notice**
>
> This guide describes a single EC2 deployment which is suitable for development, testing, or small-scale applications. For production environments, consider using:
>
> - **Amazon ECS (Elastic Container Service)** or **Kubernetes (EKS)** for:
>   - High availability through multi-AZ deployment
>   - Auto-scaling capabilities
>   - Load balancing
>   - Better resource utilization
>   - Automated container orchestration
>   - Rolling updates with zero downtime
>   - Built-in monitoring and logging
>   - Enhanced security features
>
> The single EC2 setup described here has several limitations:
> - Single point of failure
> - No auto-scaling
> - Manual deployment process
> - Limited redundancy
> - Higher maintenance overhead
>
> For production deployments, please refer to:
> - [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
> - [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)


### Launch EC2 Instance

* Go to AWS Console → EC2 → Launch Instance
* Choose Amazon Linux 2023
* Select instance type (recommended t3a.micro for this application)
* Configure Security Group:
```
Inbound Rules:
- SSH (22) from your IP
- HTTP (80) from anywhere
- HTTPS (443) from anywhere
```
* Create or select an existing key pair
* Launch instance

### Install Required Software

* Connect to your instance
```
chmod 400 keypair_portfolio_app.pem
ssh -i keypair_portfolio_app.pem ec2-user@ec2-54-76-62-87.eu-west-1.compute.amazonaws.com
```

* Install make, Docker and Docker Compose
```
# Update system
sudo yum update -y

# Install make
sudo yum install make -y

# Install Docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```
* Install Nginx
```
sudo yum install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Deploy Application

From your local machine:
```
# Create app directory on EC2
ssh -i keypair_portfolio_app.pem ec2-user@ec2-54-76-62-87.eu-west-1.compute.amazonaws.com "mkdir -p ~/app"

# Copy source code
scp -i keypair_portfolio_app.pem -r . ec2-user@ec2-54-76-62-87.eu-west-1.compute.amazonaws.com:~/app/
```

Run Docker Compose
```
# Add your user to the docker group
sudo usermod -a -G docker ec2-user

# Restart the Docker daemon
sudo systemctl restart docker

# This will start a new shell with the updated group membership
newgrp docker

cd ~/app
make up
```

### Configure Nginx

Create Nginx Configuration
```
sudo vim /etc/nginx/conf.d/app.conf
```

Add this configuration for subdomains:
```
# API subdomain
server {
    listen 80;
    server_name api.portfolio-analytics.click;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Dashboard subdomain
server {
    listen 80;
    server_name dashboard.portfolio-analytics.click;

    location / {
        proxy_pass http://localhost:8050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Test and Restart Nginx
```
sudo nginx -t
sudo systemctl restart nginx
```

### DNS Configuration

Use Route 53 or any domain registrar
In your DNS provider, create A records:
```
api.portfolio-analytics.click      → [Your EC2 Elastic IP]
dashboard.portfolio-analytics.click → [Your EC2 Elastic IP]
```

### SSL Configuration
Install Certbot
```
sudo yum install certbot python3-certbot-nginx -y
```

Obtain SSL Certificates
```
sudo certbot --nginx -d api.portfolio-analytics.click -d dashboard.portfolio-analytics.click
```
Follow the prompts to configure HTTPS.

Auto-renewal (Optional)
```
# Test auto-renewal
sudo certbot renew --dry-run

# Certbot creates a timer automatically, verify with:
sudo systemctl status certbot-renew.timer
```

### Verify Deployment

* Open your browser and navigate to:
```
https://dashboard.portfolio-analytics.click
https://api.portfolio-analytics.click
```
