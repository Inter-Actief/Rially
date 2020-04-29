# Rially

## Development environment
1. Install Docker.
1. Pull the code.
1. Run `docker-compose -f docker-compose-dev.yml up`
1. When no account is in the DB, a default account is created: admin:adminadmin
1. Open the browser at localhost.

## Production environment

1. Create a server (For example DigitalOcean, Ubuntu).
1. Run ```sudo apt-get update && sudo apt-get -y upgrade && sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - && sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && sudo apt-get update && sudo apt-get install -y docker-ce && sudo mkdir -p /ssl && sudo curl -L https://github.com/docker/compose/releases/download/1.19.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose```
1. `sudo apt-get install software-properties-common && sudo add-apt-repository ppa:certbot/certbot && sudo apt-get update && sudo apt-get install certbot && sudo certbot certonly`
1. Pull the repository (you need to give the machine pull access).
1. Add SECRET_KEY and ALLOWED_HOST to the environment field of docker-compose.yml.
1. `sudo reboot`.
1. Run `docker-compose -f docker-compose.yml up`

**NOTE:** Do not forget to add port 80 and 443 to the inbound rules of a firewall if applicable.
