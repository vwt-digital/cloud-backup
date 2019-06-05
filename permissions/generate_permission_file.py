import sys
import json

if len(sys.argv) > 1:
    project_name = sys.argv[1]
    data = {"bindings": []}

    data["bindings"].append({
        "role": "roles/storage.legacyBucketWriter",
        "members": ["serviceAccount: {}@appspot.gserviceaccount.com".format(project_name)]
    })

    with open("config/{}.json".format(project_name), 'w') as output:
        json.dump(data, output)
