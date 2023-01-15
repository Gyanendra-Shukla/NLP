from pymongo import MongoClient
import pandas as pd
import numpy as np
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from sentence_transformers import SentenceTransformer, util
from flask import Flask, request, jsonify, render_template,redirect
import pickle

class Tokenizer(object):
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_token(self, documents):
        sentences  = [documents]
        sentence_embeddings = self.model.encode(sentences)
        _ = list(sentence_embeddings.flatten())
        encod_np_array = np.array(_)
        encod_list = encod_np_array.tolist()
        return encod_list

app = Flask(__name__)

@app.route('/<INPUT>')

def fun(INPUT):
    helper_token = Tokenizer()
    # INPUT = input("Enter the Input Query ")
    token_vector = helper_token.get_token(INPUT)

    query ={
    "query": {
        "script_score": {
        "query": {
            "match_all": {}
        },
        "script": {
            "source": "cosineSimilarity(params.query_vector, 'vectors') + 1.0",
            "params": {
            "query_vector": token_vector
            }
        }
        }
    }
    }
    es = Elasticsearch("http://localhost:9200",timeout=600)
    res = es.search(index='my_index1',
                    size=15,
                    body=query,
                    request_timeout=55)

    title = [x['_source']  for x in res['hits']['hits']]
    str=''
    str=str+'Showing result for->'+INPUT+' :<br>'
    for Heading in title:
        str=str+("-" * 100)+'<br>'+'Date:'+ Heading['pubDate']+'<br>'+'Group:'+ Heading['group name']+'<br>'+'Chat:'+Heading['chat']+'<br>'
    str=str+'<br>'
    return str

if __name__ == "__main__":
    app.run(debug=True)