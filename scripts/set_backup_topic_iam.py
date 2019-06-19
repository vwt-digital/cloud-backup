from google.cloud import pubsub_v1

import logging
import sys

logging.basicConfig(level=logging.info)

if len(sys.argv) >= 3:
    project = sys.argv[1]
    topic_name = sys.argv[2]
    client = pubsub_v1.PublisherClient()
    topic_path = client.topic_path(project, topic_name)

    policy = client.get_iam_policy(topic_path)

    # Add all users as viewers.
    policy.bindings.add(
        role='roles/pubsub.publisher',
        members=["serviceAccount:{}@appspot.gserviceaccount.com".format(sys.argv[3])])

    # Set the policy
    policy = client.set_iam_policy(topic_path, policy)

    logging.info('IAM policy for topic {} set: {}'.format(topic_name, policy))
    print()
