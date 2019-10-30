sudo apt-get install apt-transport-https
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable" links gefundden auf docker.com
sudo apt-get install docker-ce docker-compose
https://hub.docker.com/r/jordan/icinga2
sudo docker pull jordan/icinga2:latest
sudo docker run -p 80:80 -h icinga2 -t jordan/icinga2:latest
