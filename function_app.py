import azure.functions as func
import logging
import json
import os
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="jftest3")
def jftest3(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )


@app.route(route="read_datalake", methods=["GET", "POST"])
def read_datalake(req: func.HttpRequest) -> func.HttpResponse:
    """
    Read files from Azure Data Lake Storage Gen2
    Expects parameters:
    - storage_account_name: The name of your storage account
    - filesystem_name: The name of your container/filesystem
    - json_file_path: Path to the JSON file in the data lake
    """
    logging.info('Reading from Azure Data Lake')
    
    try:
        # Get parameters from query string or request body
        storage_account_name = req.params.get('storage_account_name')
        filesystem_name = req.params.get('filesystem_name')
        json_file_path = req.params.get('json_file_path')
        
        if not all([storage_account_name, filesystem_name, json_file_path]):
            try:
                req_body = req.get_json()
                storage_account_name = storage_account_name or req_body.get('storage_account_name')
                filesystem_name = filesystem_name or req_body.get('filesystem_name')
                json_file_path = json_file_path or req_body.get('json_file_path')
            except ValueError:
                pass
        
        # Validate required parameters
        if not all([storage_account_name, filesystem_name, json_file_path]):
            return func.HttpResponse(
                "Missing required parameters: storage_account_name, filesystem_name, json_file_path",
                status_code=400
            )
        
        # Read local prompt files
        system_prompt = read_local_file('system.prompt.md')
        user_prompt = read_local_file('user.prompt.md')
        
        # Connect to Data Lake using Managed Identity (or DefaultAzureCredential for local dev)
        account_url = f"https://{storage_account_name}.dfs.core.windows.net"
        credential = DefaultAzureCredential()
        
        service_client = DataLakeServiceClient(account_url, credential=credential)
        file_system_client = service_client.get_file_system_client(filesystem_name)
        
        # Read JSON file from Data Lake
        json_data = read_datalake_file(file_system_client, json_file_path)
        
        # Parse JSON
        json_content = json.loads(json_data)
        
        # Prepare response
        response_data = {
            "status": "success",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "json_data": json_content,
            "metadata": {
                "storage_account": storage_account_name,
                "filesystem": filesystem_name,
                "json_file": json_file_path
            }
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error reading from Data Lake: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


def read_local_file(file_path: str) -> str:
    """Read a local file and return its contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Local file not found: {file_path}")
        return ""
    except Exception as e:
        logging.error(f"Error reading local file {file_path}: {str(e)}")
        return ""


def read_datalake_file(file_system_client, file_path: str) -> str:
    """Read a file from Azure Data Lake and return its contents"""
    file_client = file_system_client.get_file_client(file_path)
    download = file_client.download_file()
    return download.readall().decode('utf-8')
