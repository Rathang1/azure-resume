import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to update visitor count.')

    # Cosmos DB connection details
    endpoint = os.environ["AzureResumeEndPoint"]
    key = os.environ["AzureResumeConnectionString"]
    
    # Initialize Cosmos Client
    client = CosmosClient(endpoint, key)
    database_name = 'TablesDB'  # Update with your database name
    database = client.get_database_client(database_name)
    container_name = 'VisitorCount'  # Update with your container name
    container = database.get_container_client(container_name)

    # Query to get the current visitor count
    query = "SELECT * FROM c WHERE c.id='VisitorCount'"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if items:
        # Get the current count value
        count_value = items[0]['count']
        
        # Increment the $v value as int32
        new_v_value = int(count_value['$v']) + 1  # Incrementing the $v value

        # Update the count with the new values
        items[0]['count'] = {'$t': count_value['$t'], '$v': new_v_value}

        # Replace the entire document in the database
        container.replace_item(item=items[0]['id'], body=items[0])

        # Send back only the new visitor count
        return func.HttpResponse(body=json.dumps(new_v_value), mimetype="application/json", status_code=200)
    else:
        return func.HttpResponse("No items found", status_code=404)
