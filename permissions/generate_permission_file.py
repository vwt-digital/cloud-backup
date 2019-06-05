import base64
import sys
import json

if len(sys.argv) > 1:
    project_name = sys.argv[1]
    etag = base64.b64encode(project_name.encode('utf-8'))

    data = {"bindings": [], "etag": str(etag)[2:-1]}

    data["bindings"].append({
        "role": "roles/storage.legacyBucketWriter",
        "members": ["serviceAccount: {}@appspot.gserviceaccount.com".format(project_name)]
    })

    with open("config/{}.json".format(project_name), 'w') as output:
        json.dump(data, output)
