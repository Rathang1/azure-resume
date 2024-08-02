import logging
import json
import os
import azure.functions as func
from azure.cosmos import CosmosClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request to update visitor count.')

    try:
        # Cosmos DB connection details
        endpoint = os.environ.get("AzureResumeEndPoint")
        key = os.environ.get("AzureResumeConnectionString")
        
        if not endpoint or not key:
            logging.error("Cosmos DB endpoint or key is missing.")
            return func.HttpResponse("Cosmos DB endpoint or key is missing.", status_code=500)

        logging.info('Cosmos DB endpoint and key retrieved from environment variables.')

        # Initialize Cosmos Client
        client = CosmosClient(endpoint, key)
        logging.info('Cosmos Client initialized.')

        database_name = 'TablesDB'  # Update with your database name
        container_name = 'VisitorCount'  # Update with your container name
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        logging.info(f'Connected to database: {database_name}')
        logging.info(f'Connected to container: {container_name}')

        # Query to get the current visitor count
        query = "SELECT * FROM c WHERE c.id='VisitorCount'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        logging.info('Executed query to retrieve current visitor count.')

        if items:
            # Get the current count value
            count_value = items[0]['count']
            logging.info(f'Current count value retrieved: {count_value}')

            # Increment the $v value as int32
            new_v_value = int(count_value['$v']) + 1  # Incrementing the $v value
            logging.info(f'Incremented $v value: {new_v_value}')

            # Update the count with the new values
            items[0]['count'] = {'$t': count_value['$t'], '$v': new_v_value}
            logging.info(f'Updated count value: {items[0]["count"]}')

            # Replace the entire document in the database
            container.replace_item(item=items[0]['id'], body=items[0])
            logging.info('Replaced the document with updated count in the database.')

            # Send back only the new visitor count
            return func.HttpResponse(body=json.dumps(new_v_value), mimetype="application/json", status_code=200)
        else:
            logging.error('No items found in the database for the given query.')
            return func.HttpResponse("No items found", status_code=404)
    except Exception as e:
        logging.error(f'An error occurred: {str(e)}', exc_info=True)
        return func.HttpResponse(f'An error occurred: {str(e)}', status_code=500)
