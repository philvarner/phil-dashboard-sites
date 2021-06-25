""" Sites generator """
from model import Site
from typing import Any, Dict, List
from pydantic import ValidationError
import json
import os

import boto3
import yaml
import html5lib

BASE_PATH = os.path.abspath('.')
config = yaml.load(open(f"{BASE_PATH}/config.yml", "r"), Loader=yaml.FullLoader)

SITES_INPUT_FILEPATH = os.path.join(BASE_PATH, "sites")

SITES_OUTPUT_FILENAME = f"{os.environ.get('STAGE', 'local')}-site-metadata.json"


def create_sites_json():
    """
    Returns:
    -------
    (string): JSON object containing a list of all sites. This is the output of the 
        `/sites` endpoint.
    """

    sites = _gather_data(dirpath=SITES_INPUT_FILEPATH, visible_sites=config['SITES'])

    s3 = boto3.resource("s3")
    bucket = s3.create_bucket(Bucket=os.environ.get("DATA_BUCKET_NAME", config.get('BUCKET')))
    bucket.put_object(
        Body=json.dumps(sites), Key=SITES_OUTPUT_FILENAME, ContentType="application/json",
    )

    return sites 


def _gather_data(dirpath: str, visible_sites: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Gathers site info and creates a JSON structure from it"""
    parser = html5lib.HTMLParser(strict=True)

    results = []
    for path in os.walk(dirpath):
        site = path[0].rsplit("/", 1)[1]
        if visible_sites and site not in visible_sites and site != "global":
            continue
        with open(os.path.join(dirpath, site, "site.json"), "r") as f:
            entity = json.loads(f.read())
            if site != "global":
                try:
                    Site(**entity)
                except ValidationError as e:
                    print(f"Error processing site.json for {site}: {e.json()}")
                    raise e
        with open(os.path.join(dirpath, site, "summary.html"), "r") as f:
            summary = f.read()
            parser.parseFragment(summary)
            entity["summary"] = summary
        results.append(entity)    
    return {"sites" : results }

if __name__ == "__main__":
    print(json.dumps(create_sites_json()))
