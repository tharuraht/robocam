import json
import argparse


parser = argparse.ArgumentParser(description="Basic script to open json file and print value")
parser.add_argument('machine', type=str, help='Machine conf to access')
parser.add_argument('field', type=str, help='Field of conf to print')
parser.add_argument('-j', '--json_path', type=str, default='robocam_conf.json', help='path to JSON file')


args = parser.parse_args()
with open(args.json_path) as f:
    data = json.load(f)
    print(data[args.machine][args.field])
