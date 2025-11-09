# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-west-2.amazonaws.com
docker build -t sworms-lite .
docker tag sworms-lite:latest <account_id>.dkr.ecr.us-west-2.amazonaws.com/sworms-lite:latest
docker push <account_id>.dkr.ecr.us-west-2.amazonaws.com/sworms-lite:latest