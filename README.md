# EC2 Hunter

Finds all EC2 instances in the AWS accounts defined in your AWS CLI profiles.

The program will parse your AWS CLI config file for the available profiles, and search all available AWS regions per profile for EC2 instances, regardless of their running state.

By default, output is sent to the console in JSON format. You can write to a json file with the `-w` option.

## Usage

```
usage: ec2-hunter.py [-h] [-e [EXCLUDE ...]] [-l LIMIT] [-w]

optional arguments:
  -h, --help            show this help message and exit
  -e [EXCLUDE ...], --exclude [EXCLUDE ...]
                        AWS CLI profiles to exclude.
  -l LIMIT, --limit LIMIT
                        Limit to a specific AWS CLI profile.
  -w, --write           Write output to ./ec2_instances.json file.
```

### Pip

```
python3 -m venv venv
source venv/bin/activate
pip insall -r requirements.txt
python3 ec2-hunter.py [OPTIONS]
```

### Poetry

```
poetry install
poetry run python ec2-hunter.py [OPTIONS]
```
