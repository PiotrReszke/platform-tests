REPO_PATH=$(pwd)
sudo apt-get install libssl-dev
cd /tmp && wget https://github.com/AGWA/git-crypt/archive/0.5.0.zip
unzip 0.5.0.zip && cd git-crypt-0.5.0/
make && sudo make install

cd $REPO_PATH && git-crypt unlock key.dat
