from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from functools import wraps
from mysql_con import check_credentials
import json
import os
import socket

es_ip = socket.gethostbyname(os.environ.get('ES_IP'))
app = Flask(__name__)
es = Elasticsearch([f'http://{es_ip}:9200'])

def authenticate(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        usern = request.headers.get("username")
        pwd = request.headers.get("password")
        if check_credentials(usern,pwd):
            return func(*args, **kwargs)

        return jsonify({'error': 'Unauthorized'}), 401
    return wrapper_func


#================================================================================================================

@app.route('/create_index/<index_name>', methods= ['PUT'])
@authenticate
def create_index(index_name):
    try:
        data = dict(request.get_json())
        print(data)
        dic_data = dict()
        for key,val in data.items():
            print(key)
            dic_data[key] = {"type" : val}
        print(dic_data)
        mapping = {
            "mappings" : {
                "properties": dic_data,
                "dynamic" : "strict"
            }
        }
        print(mapping)
        try:
            es.indices.create(index=index_name, body=mapping)
            return jsonify({
                "status" : "successful",
                "message" : f'{index_name} created with respective mappings'
            })
        except Exception as e: 
            return jsonify({
                "status" : "unsuccessful",
                "message" : str(e)
            })

    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500

#================================================================================================================

@app.route('/get_doc/<index_name>/<doc_id>', methods=['GET'])
@app.route('/get_doc/<index_name>/', methods=['GET'])
@authenticate
def get_document(index_name, doc_id=None):
    try:
        if doc_id is not None:
            if es.exists(index=index_name, id=doc_id):
                result = es.get(index=index_name, id=doc_id)
                document = result['_source']
                return jsonify(document), 200
            else:
                return jsonify({"error": f"Doc ID '{doc_id}' does not exist in index '{index_name}'"}), 404
        else:
            result = es.search(index=index_name, body={"query": {"match_all": {}}})
            documents = [hit['_source'] for hit in result['hits']['hits']]
            return jsonify(documents), 200
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


@app.route('/get_by_query/<index_name>', methods=['GET'])
@authenticate
def get_by_query(index_name):
    try:
        search_query = request.get_json()
        if not search_query:
            return jsonify({"error": "query input required"}), 400
        result = dict(es.search(index=index_name, body=search_query))
        documents = [hit['_source'] for hit in result['hits']['hits']]
        return jsonify({"documents": documents}), 200
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


#=================================================================================================================

@app.route('/ingest_doc/<index_name>', methods=['POST'])
@authenticate 
def ingest_document(index_name):
    try:
        data = request.get_json()
        dic_data = dict(data)
        print(dic_data.keys())
        res = dict(es.index(index=index_name, body=data))
        if res['result'] == 'created':
            return jsonify({"message": "Document successfully ingested", "es_response": res}), 200
        else:
            return jsonify({"error": "Failed to ingest document", "es_response": res}), 500
    except Exception as e:
        print(str(e))
        error_message = {'error': str(e)}
        return jsonify(error_message), 500  # Use 500 status code for server errors


@app.route('/ingest_bulk/<index_name>', methods=['POST'])
@authenticate
def ingest_bulk_data(index_name):
    try:
        # Check if the request contains a file with the key 'file'
        print(request.files) #ImmutableMultiDict([('file', <FileStorage: 'data.json' ('application/json')>)])
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        # Check if the file has an allowed extension (e.g., .json)
        allowed_extensions = {'json'}
        print(file) # <FileStorage: 'data.json' ('application/json')>
        print(file.filename) # data.json
        print(file.filename.rsplit(".",1))
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({"error": "Invalid file extension. Allowed extensions: .json"}), 400
        # Load JSON data from the file
        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid JSON format in the file: {str(e)}"}), 400
        # Ingesting bulk data into Elasticsearch
        success_count = 0
        failure_count = 0
        fail_response = {}
        for ind,doc in enumerate(data):
            print(doc)
            try:
                es.index(index=index_name, body=doc)
                success_count += 1
            except Exception as e:
                fail_response[str(ind)] = str(e)
                failure_count += 1
        return jsonify({
            "successfully uploaded documents": success_count, 
            "total_documents": len(data), 
            "failed Documents " : failure_count ,
            "failed reasons" : fail_response
        }), 200
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


#=================================================================================================================

#deletion with document ID
@app.route('/delete_doc/<index_name>/<doc_id>', methods=['DELETE'])
@authenticate
def delete_document(index_name, doc_id):
    try:
        if es.exists(index=index_name, id=doc_id):
            res = dict(es.delete(index=index_name, id=doc_id))
            if res['result'] == 'deleted' :
                return jsonify({
                    "message" : res,
                    "document_name" : doc_id,
                    "index_name" : index_name,
                    "deletion" : "successful"
                }),200
            else:
                return jsonify({
                    "message" : res,
                    "index" : index_name,
                    "deletion" : "unsuccessful"
                }),500
        else:
            return jsonify({"error": f"Document with ID '{doc_id}' does not exist in index '{index_name}'"}), 404
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


@app.route('/delete_by_query/<index_name>', methods=['DELETE'])
@authenticate
def delete_by_query(index_name):
    try:
        query = request.get_json()
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        response = dict(es.delete_by_query(index=index_name, body=query))
        print(response)
        
        """
        {'took': 24, 'timed_out': False, 'total': 14, 'deleted': 14, 'batches': 1, 
        'version_conflicts': 0, 'noops': 0, 'retries': {'bulk': 0, 'search': 0}, 
        'throttled_millis': 0, 'requests_per_second': -1.0, 'throttled_until_millis': 0, 
        'failures': []}
        """
        if response['deleted']:
            return jsonify({
                "message": f"Documents matching the query successfully deleted from index '{index_name}'",
                "deleted": response['deleted'],
                "took": response['took'],
                'total_match': response['total']
            }), 200
        else:
            return jsonify({
                "message": "No matching documents found to delete in index",
                "error_message": response
            }), 500
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


#=================================================================================================================

@app.route('/update_doc/<index_name>/<doc_id>', methods=['POST'])
@app.route('/update_by_query/<index_name>', methods=['POST'])
@authenticate
def update_by_query(index_name,doc_id=None):
    try:
        if doc_id:
            if es.exists(index=index_name, id=doc_id):
                update_data = request.get_json()
                if not update_data:
                    return jsonify({"error": "Update data parameter is required"}), 400
                response = es.update(index=index_name, id=doc_id, body={"doc": update_data})
                if 'result' in response and response['result'] == 'updated':
                    return jsonify({"message": f"Document with ID '{doc_id}' successfully updated in index '{index_name}'"}), 200
                else:
                    return jsonify({"error": f"Failed to update document with ID '{doc_id}' in index '{index_name}'"}), 500
            else:
                return jsonify({"error": f"Document with ID '{doc_id}' does not exist in index '{index_name}'"}), 404
        else:
            update_query = request.get_json()
            print(update_query)
            if not update_query:
                return jsonify({"error": "Update query parameter is required"}), 400
            response = dict(es.update_by_query(index=index_name, body=update_query))
            print(response)
            if response['updated']:
                return jsonify({
                    "Result": f"Documents matching the query successfully updated in index '{index_name}'",
                    "Response Body": response
                }), 200
            else:
                return jsonify({"error": "Failed to perform update by query"}), 500
    except Exception as e:
        error_message = {'error': str(e)}
        return jsonify(error_message), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)