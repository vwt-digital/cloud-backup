import json
import sys


if len(sys.argv) > 1:
    back_up_topic = sys.argv[1]
    result = {
        'bindings': [
            {
                'members': [],
                'role': 'roles/pubsub.publisher'
            }
        ]
    }

    result['bindings'][0]['members'].append('serviceAccount:{}@appspot.gserviceaccount.com'.format(back_up_topic))

    print(json.dumps(result))

