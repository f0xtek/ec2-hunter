#!/usr/bin/env python
import boto3
import boto3.session
import botocore.exceptions
import json
import sys
import re
from pathlib import Path
from argparse import ArgumentParser

CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'


class ProfileNotFoundException(Exception):
    pass


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-e', '--exclude', nargs='*',
                        help='AWS CLI profiles to exclude.')
    parser.add_argument('-l', '--limit', type=str,
                        default=None,
                        help='Limit to a specific AWS CLI profile.')
    parser.add_argument('-w', '--write', action='store_true',
                        help='Write output to ./ec2_instances.json file.')
    return parser.parse_args()


def get_aws_profiles(excludes, limit):
    try:

        home_dir = str(Path.home())
        with open(f'{home_dir}/.aws/config', 'r') as f:
            lines = f.readlines()

        pattern = '(?<=\[profile )\S*(?=\])'
        profiles = re.findall(pattern, '\n'.join(lines))

        if not profiles:
            print(f'❗  No AWS CLI profiles found!')
            sys.exit(1)

        if limit is not None:
            if limit in profiles:
                return [limit]
            else:
                raise ProfileNotFoundException(
                    f'❗  AWS CLI profile {limit} does not exist!')

        if excludes is not None:
            [profiles.remove(exclude)
             for exclude in excludes if exclude in profiles]
        return profiles
    except OSError as err:
        print("❗  Unable to read AWS CLI profiles from config file!")
        print(err)
    except ProfileNotFoundException as err:
        print(err)
        sys.exit(1)


def get_regions(client):
    try:
        regions = []
        regions_list = client.describe_regions()['Regions']
        [regions.append(region['RegionName']) for region in regions_list]
        return regions
    except botocore.exceptions.ClientError as err:
        print(err.response["Error"]["Code"])
        print(err.response["Error"]["Message"])
        pass


def get_instances_in_region(sess, region):
    try:
        ec2 = sess.resource('ec2', region_name=region)
        return list(ec2.instances.all())
    except botocore.exceptions.ClientError as err:
        print(err.response["Error"]["Code"])
        print(err.response["Error"]["Message"])


def write_file(data):
    try:
        filename = 'ec2_instances.json'
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=2))
            print("✅ Complete!")
            print(f"✍️  Final results written to {filename}")
    except OSError as err:
        print("❗  Unable to write to file!")
        print(err)


def print_instances_output(data, write_to_file):
    if write_to_file:
        write_file(data)
    else:
        print("\n", json.dumps(data, indent=2))


def main():
    instances_per_region = {}
    args = parse_args()

    if args.exclude is not None:
        if args.limit is not None:
            print("❗  Cannot set both exclude and limit!")
            sys.exit(1)
        excluded_aws_profiles = args.exclude
        profile_limit = None
    elif args.limit is not None:
        profile_limit = args.limit
        excluded_aws_profiles = None
    else:
        excluded_aws_profiles = None
        profile_limit = None

    aws_profiles = get_aws_profiles(excluded_aws_profiles, profile_limit)

    for aws_profile in aws_profiles:
        print("ℹ️  Working with AWS Profile: " + aws_profile)
        session = boto3.session.Session(profile_name=aws_profile)
        ec2_client = session.client('ec2')
        aws_regions = get_regions(ec2_client)

        instances_per_region[aws_profile] = {}

        for aws_region in aws_regions:
            print(f"🔎 Hunting for instances in {aws_region}")
            sys.stdout.write(CURSOR_UP_ONE)
            sys.stdout.write(ERASE_LINE)
            instance_objects = get_instances_in_region(session, aws_region)

            if len(instance_objects) > 0:
                print(f"✅ Found instances in {aws_region}!")
                instances_per_region[aws_profile][aws_region] = {}

                for instance_object in instance_objects:
                    instance_tags = instance_object.tags
                    if instance_tags is not None:
                        for tag in instance_tags:
                            if tag["Key"].lower() == "name":
                                instance_name = tag["Value"]
                            else:
                                instance_name = ""
                    else:
                        instance_name = ""
                    instances_per_region[aws_profile][aws_region][instance_object.id] = {
                        "instance_type": instance_object.instance_type,
                        "instance_name": instance_name
                    }
            else:
                continue
    print_instances_output(instances_per_region, args.write)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(end="\r")
        pass
