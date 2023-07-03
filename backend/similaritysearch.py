from flask import Flask, request
from dotenv import load_dotenv
from googletrans import Translator
load_dotenv()
from flask_cors import CORS
import cohere
import openai
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
import pandas as pd 
import os 

cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
model_id = "text-embedding-ada-002"
#model_id='embed-multilingual-v2.0'
coherekey = os.environ.get('coherekey')
openai.api_key = open_api_key
co = cohere.Client(coherekey)
translator = Translator(service_urls=['translate.googleapis.com'])
cloud_config= {
  'secure_connect_bundle': scb_path
}

auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)

app = Flask(__name__)
CORS(app)


@app.route('/similaritems', methods=['POST'])
def ann_similarity_search():
    #customer_query='สีที่ดีที่ละลายได้อย่างสวยงาม'
    customer_query = request.json.get('newQuestion')
    #english_customer_text= translator.translate(customer_query)
    #print(english_customer_text.text)
    
    customer_text = []
    customer_text.append(customer_query)
    #response = co.embed(texts=customer_text, model=model_id)
    embeddings = openai.Embedding.create(input=customer_query, model=model_id)['data'][0]['embedding']
   # embeddings = response.embeddings[0]
    query = SimpleStatement(
    f"""
    SELECT *
    FROM {keyspace}.{table_name}
    ORDER BY openai_description_embedding ANN OF {embeddings} LIMIT 5;
    """
    )
      

    results = session.execute(query)
    top_5_products = results._current_rows
    response = []
    for r in top_5_products:
        response.append({
            'id': r.product_id,
            'name': r.product_name,
            'description': r.description,
            'price': r.price
        })
    print(response)

    message_objects = []
    message_objects.append({"role":"system",
                            "content":"You're a chatbot helping customers with questions and helping them with product recommendations"})

    message_objects.append({"role":"user",
                            "content":customer_query})

    message_objects.append({"role":"user",
                            "content": "Please give me a detailed explanation of your recommendations"})

    message_objects.append({"role":"user",
                            "content": "Please be friendly and talk to me like a person, don't just give me a list of recommendations"})

    message_objects.append({"role": "assistant",
                            "content": "I found these 3 products I would recommend"})

    products_list = []

    for row in response:
        #trans= translator.translate(row.description)
        brand_dict = {'role': "assistant", "content": f"{row['id']}, {row['description']}, {row['name']}, {row['price']}"}
        products_list.append(brand_dict)

    message_objects.extend(products_list)
    message_objects.append({"role": "assistant", "content":"Here's my summarized recommendation of products, and why it would suit you:"})

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=message_objects
    )

    human_readable_response = completion.choices[0].message['content']
    print(human_readable_response)
    #thai_response=translator.translate(human_readable_response, dest='th')

    values = dict()
    values['products'] = response
    values['botresponse'] = human_readable_response

    return values

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)