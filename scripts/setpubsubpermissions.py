import sys
from google.cloud import pubsub_v1

client = pubsub_v1.PublisherClient()

if len(sys.argv) >= 3:
    project = sys.argv[1]
    topic_name = sys.argv[2]

    topic_path = client.topic_path(project, topic_name)
    policy = client.get_iam_policy(topic_path)

    # Add a group as a publisher.
    policy.bindings.add(
        role='roles/pubsub.publisher',
        members=['{}@appspot.gserviceaccount.com'.format(sys.argv[3])])

    # Set the policy
    policy = client.set_iam_policy(topic_path, policy)
