from pymongo import MongoClient
import pandas as pd
import numpy as np
import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from sentence_transformers import SentenceTransformer, util
from flask import Flask, request, jsonify, render_template,redirect
import pickle

app = Flask(__name__)

@app.route('/<INPUT>')

def fun(INPUT):
    client=MongoClient("mongodb+srv://emseccomandcenter:TUXnEN09VNM1drh3@cluster0.psiqanw.mongodb.net/?retryWrites=true&w=majority")

    db=client['webScraping']

    collection=db["rohan"]

    f=list(collection.find())

    df=pd.DataFrame(f)
    df=df.loc[:,'Heading':'Content']

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

    class ElasticSearchImports(object):
        def __init__(self, df, index_name='my_index'):
            self.df = df
            self.index_name = index_name
            self.es = Elasticsearch("http://localhost:9200",timeout=600)

        def run(self):

            elk_data = self.df.to_dict("records")

            for alldata in elk_data:
                try:self.es.index(index=self.index_name,body=alldata)
                except Exception as e:pass

            return True

    helper_token = Tokenizer()
    df["vectors"] = df["Heading"].apply(helper_token.get_token)



    helper_elk = ElasticSearchImports(df=df)
    helper_elk.run()

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
    res = es.search(index='my_index',
                    size=15,
                    body=query,
                    request_timeout=55)

    title = [x['_source']  for x in res['hits']['hits']]
    str=''
    str=str+'Showing result for->'+INPUT+' :<br>'
    for Heading in title:
        str=str+("-" * 100)+'<br>'+'Date:'+ Heading['Date']+'<br>'+'Heading:'+ Heading['Heading']+'<br>'+'Content:'+Heading['Content']+'<br>'
    str=str+'<br>'
    return str
# print(fun('Dixons Allerton Academy'))
if __name__ == "__main__":
    app.run(debug=True)
