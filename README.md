# FlaskAPI-to-interact-with-ElasticSearch

# overview of flask API created below:

# get command :

get by Id: @app.route('/get_doc/<index_name>/<doc_id>', methods=['GET']) 

get all documents in index: @app.route('/get_doc/<index_name>/', methods=['GET'])

get by query : @app.route('/get_by_query/<index_name>', methods=['GET'])

json:
{    
  "query": {  
    "match": {  
        key : value 
    }  
  }  
} 


# ingest Commands:

ingest single doc : @app.route('/ingest_doc/<index_name>', methods=['POST'])

ingest bulk file : @app.route('/ingest_bulk/<index_name>', methods=['POST'])

# delete commands:

delete by ID : @app.route('/delete_doc/<index_name>/<doc_id>', methods=['DELETE'])

delete by query : @app.route('/delete_by_query/<index_name>', methods=['DELETE'])

{    
  "query": {  
    "match": {  
        key : value 
    }  
  }  
} 


# update commands:

update by id : @app.route('/update_by_query/<index_name>/<doc_id>', methods=['POST'])

update by query : @app.route('/update_by_query/<index_name>', methods=['POST'])

{  
"script": {  
    "inline": "ctx._source.key=value",  
    "lang": "painless"  
  },  
  "query": {  
    "match": {  
        key: value  
    }  
  }  
}  

