## Running api tests

### Requirements
* Recommended OS - Ubuntu 14
* access to the Web (several tests rely on Web resources)
* key `key.dat` to decrypt repository secrets (ask repository owner)


### Setup

**1. Access to cdh launcher**
```
cp <private/key/of/ec2-user> ~/.ssh/auto-deploy-virginia.pem
```
Unfortunately, tests currently use a hardcoded path.

**2. Install required packages**
```
sudo apt-get install python3 python3-dev git
```

**3. Download and install git crypt**
```
wget https://github.com/AGWA/git-crypt/archive/0.5.0.zip
unzip 0.5.0.zip
cd git-crypt-0.5.0
make git-crypt
sudo make install git-crypt
```

**4. Clone repository**
```
git clone git@github.com:intel-data/api-tests.git
```

**5. Decrypt repository secrets**

Place `key.dat` in api-tests directory.
```
cf api-tests
./deploy/unlock.sh
```
Check that secrets are decrypted correctly:
```
cat api-tests/project/test_utils/secrets/.secret.ini
```
If the file looks normal, secrets have been decrypted.

**6. Set up virtualenv**
```
./deploy/create_virtualenv.sh
```
This will create [pyvenv](https://docs.python.org/3/using/scripts.html) with all Python packages required in `~/virtualenvs/pyvenv_api_tests`.

**7. Add config** -- only if environment has non-default configuration (e.g. no seedorg)

If you plan to run tests on a new environment (i.e. not daily, sprint, demo, etc.), supply non-default config values in `api-tests/project/test_utils/config.py`, in `__CONFIG` string.

**8. Configure test admin user** -- only if it's not already present on an environment

To run tests, we need a user trusted.analytics.tester@gmail.com with appropriate roles and authorizations. To create such user, use script `api-tests/deploy/create_test_admin.sh`. The script requires cf client and uaac.

install cf client
```
wget https://cli.run.pivotal.io/stable?release=debian64 -O cf-client.deb
sudo dpkg -i cf-client.deb
```

install uaac
```
sudo apt-get install rubygems-integration
sudo gem install cf-uaac
```

run the script
```
create_test_admin.sh <domain> <cf admin password> <reference org name> <reference space name> <password>
```
- domain, e.g. gotapaas.eu
- cf admin password -- cf password of user admin
- reference org name (defaults to seedorg)
- reference space name (defaults to seedspace)
- password (see password for trusted.analytics.tester@gmail.com in DEFAULT section in `api-tests/project/test_utils/secrets/.secret.ini`)


### Run tests
1. Activate virtualenv: `source ~/virtualenvs/pyvenv_api_tests/bin/activate`.
2. `cd api-tests/project`
3. Run tests using `run_tests.sh` script (see below).

To run smoke tests:
`./run_tests.sh -e <domain, e.g. demotrustedanalytics.com> -s test_smoke > <log_file> 2>&1`

To run api tests:
`./run_tests.sh -e <domain, e.g. demotrustedanalytics.com> -s test_api > <log_file> 2>&1`


**Parameters**

`-s` - run tests from one directory or file, e.g. `./run_tests.sh -e <domain> -s <path/in/tests/directory>`.

`-t` - run single test: `./run_tests.sh -e <domain> -t <test_name>`, for example: `-t test_create_organization`.

`--proxy` - use proxy address with port, e.g. `--proxy proxy-mu.intel.com:911`. If you omit this parameter, requests will use http/https proxy retrieved from system settings.

`-l` - specify logging level. There are 3 logging levels: DEBUG (default), INFO `-l INFO`, WARNING `-l WARNING`.

The `run_tests.sh` shell script is used only to run_tests.py in a virtual environment, passing all arguments to the Python script. If you want to see/modify what is happening when tests are run, go there. Argument parsing function is located in project/test_utils/config.py

Tests log to both stdout, and stderr, so to save output to a file, use `> <log_file> 2>&1`.


### Run tests on TeamCity agent

Before tests are run on TeamCity:

Required packages (see above) should be installed on the agent.

On TeamCity, a few Command Line custom script steps need to be defined:

Decrypt repository secrets: `git-crypt unlock %decryptor.key.path%`

Create virtualenv `./deploy/create_virtualenv.sh`

Appstack tests `./project/run_tests.sh -s "test_appstack" -e %test_platform%`

API tests: `./project/run_tests.sh -s %test_type% -e %test_platform% --client-type "$client_type"`

Application tests: `./project/run_tests.sh -s "test_cf_applications" -e %test_platform%`

### Run smoke tests on bastion

Ssh to your bastion using most likely auto-deploy-virginia.pem key (if you don't know bastion address, but you know the environment is deployed automatically on TeamCity, you'll find bastion address in platform-deployment-tests/deployment-init configuration, step Update domain IP addresses)

Required packages (```sudo apt-get install python3 python3-dev git```) should be installed on the bastion.

Install git-crypt and decrypt repository secrets:
```
wget https://github.com/AGWA/git-crypt/archive/0.5.0.zip
unzip 0.5.0.zip
cd git-crypt-0.5.0
make git-crypt
sudo make install git-crypt
```

Copy your github private key to bastion and add it to shh:
```
scp -i ./auto-deploy-virginia.pem [your_private_key] [user]@[bastion_address]:/[path_to_ssh]/.ssh/[your_private_key]
eval `ssh-agent`
ssh-add .ssh/[your_private_key]
```
Check if it works: `ssh -vT git@github.com`

Create folder for tests 
```
mkdir [tests_folder_name]
cd [tests_folder_name]
```
Clone repository: `git clone git@github.com:intel-data/api-tests.git`

Copy key.dat into api-tests folder: `scp -i ./auto-deploy-virginia.pem [path_to_key]/key.dat  [user]@bastion_address:/[path_to_tests_folder]/api-tests`

Decrypt repository secrets:
```
cd [tests_folder_name]/api-test
./deploy/unlock.sh
```
Check that secrets are decrypted correctly: `cat api-tests/project/test_utils/secrets/.secret.ini`

Create virtualenv: `./deploy/create_virtualenv.sh`. 
New Folder virtualenvs/ should be visible in home directory

Create test user if not already present: `trusted.analytics.tester@gmail.com` (see above for details)

Run smoke tests
```
cd [tests_folder_name]/api-test
./project/run_tests.sh -s test_smoke -e [platform_address] > [log_file] 2>&1
```
