## Running api tests

#### Requirements
* apt packages required: python3 python3-dev git git-crypt
* key to decrypt repository secrets (ask repository owner)
* access to the Web (to download appstack.yml, to download pip from https://bootstrap.pypa.io/get-pip.py and other python packages, to access links for transfer creation)
* private key of cdh launcher in `~/.ssh/auto-deploy-virginia.pem`
* User trusted.analytics.tester@gmail.com with appropriate roles and authorizations. To create such user, use script `api-tests/deploy/create_test_admin.sh`

#### Setup
1. Clone the repository and `cd api-tests`.
2. Decrypt secrets. In api-tests directory run `./deploy/unlock.sh`.
3. Set up virtualenv `./deploy/create_virtualenv.sh`. This script will create virtualenv with all Python packages required in `~/virtualenvs/pyvenv_api_tests`.
4. If you plan to run tests on a new environment (i.e. not daily, sprint, demo, etc.), supply non-default config values in `api-tests/project/test_utils/config.py`, in `__CONFIG` string.

#### Run tests
1. Activate virtualenv: `source ~/virtualenvs/pyvenv_api_tests/bin/activate`.
2. `cd api-tests/project`
3. Run tests using `run_tests.sh` script (see below).

To run all tests:
`./run_tests.sh -e <domain, e.g. demotrustedanalytics.com>`

This shell script is used only to run_tests.py in a virtual environment, passing all arguments to the Python script. If you want to see/modify what is happening when tests are run, go there. Argument parsing function is located in project/test_utils/config.py
Tests log to both stdout, and stderr, so to save output to a file, use `> <log_file> 2>&1`.

**-s**
To run tests from one directory or file, use -s: `./run_tests.sh -e <domain> -s <path/in/tests/directory>`.
For example, to run only smoke tests, use `-s test_appstack`, to run only api tests, use: `-s test_api`, to run only user-management tests, use `-s test_api/user_management`, to run only onboarding tests, use `-s test_api/user_management/test_onboarding.py`.

**-t**
To run single test: `./run_tests.sh -e <domain> -t <test_name>`.
For example: `-t test_create_organization`.

**--proxy**
If you omit this parameter, requests will use http/https proxy retrieved from system settings.
If you want to specify proxy, use proxy address with port, e.g. `--proxy proxy-mu.intel.com:911`

**-l**
There are 3 logging levels: DEBUG (default), INFO `-l INFO`, WARNING `-l WARNING`.


#### Run tests on TeamCity agent

Before tests are run on TeamCity:

Required packages (see above) should be installed on the agent.

On TeamCity, a few Command Line custom script steps need to be defined:

Decrypt repository secrets: `git-crypt unlock %decryptor.key.path%`

Create virtualenv `./deploy/create_virtualenv.sh`

Appstack tests `./project/run_tests.sh -s "test_appstack" -e %test_platform%`

API tests: `./project/run_tests.sh -s %test_type% -e %test_platform% --client-type "$client_type"`

Application tests: `./project/run_tests.sh -s "test_cf_applications" -e %test_platform%`
