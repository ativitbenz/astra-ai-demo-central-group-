from dotenv import load_dotenv
import cohere
load_dotenv()
import openai
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
import pandas as pd 
import numpy as np
import os 

cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
data_file = os.environ.get('data_file')
coherekey = os.environ.get('coherekey')
#model_id = hub.KerasLayer("https://tfhub.dev/google/universal-sentence-encoder-multilingual/3", trainable=False)
model_id='embed-multilingual-v2.0'
openai.api_key = open_api_key
co = cohere.Client(coherekey)
cloud_config= {
  'secure_connect_bundle': scb_path
}

auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)

df = pd.read_csv(data_file)

products_list = df.replace(np.nan, '', regex=True)

#print(products_list)

session.execute(f"""CREATE TABLE IF NOT EXISTS {keyspace}.{table_name}
(product_id int,
 chunk_id int,
 title text,
 description text,
 link text,
 imagelink text,
 availability text,   
 price text,
 brand text,
 condition text,
 producttype text,
 saleprice text,                                              
 openai_description_embedding vector<float, 768>,
 minilm_description_embedding vector<float, 384>,
 PRIMARY KEY (product_id,chunk_id))""")

# # Create Index
session.execute(f"""CREATE CUSTOM INDEX IF NOT EXISTS openai_desc ON {keyspace}.{table_name} (openai_description_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'""")
session.execute(f"""CREATE CUSTOM INDEX IF NOT EXISTS minilm_desc ON {keyspace}.{table_name} (minilm_description_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'""")
session.execute(f"""CREATE CUSTOM INDEX IF NOT EXISTS title_index ON {keyspace}.{table_name} (title) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'""")


for id, row in products_list.iterrows():
  # Create Embedding for each conversation row, save them to the database
  text_chunk_length = 2500
  text_chunks = [row.description[i:i + text_chunk_length] for i in range(0, len(row.description), text_chunk_length)]
  for chunk_id, chunk in enumerate(text_chunks):
    pricevalue = row.price if isinstance(row.price, str) else ""
    full_chunk = []
    full_chunk.append(f"{chunk} price: {pricevalue}")
    #embedding = openai.Embedding.create(input=full_chunk, model=model_id)['data'][0]['embedding']
    #print(full_chunk)
    response = co.embed(texts=full_chunk, model=model_id) 
    embeddings = response.embeddings[0]
    #print(embeddings)
    query = SimpleStatement(
                f"""
                INSERT INTO {keyspace}.{table_name}
                (product_id, chunk_id, title, description, link, imagelink,availability, price, brand, condition,producttype,saleprice,openai_description_embedding)
                VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s)
                """
            )
    print(row)
    
    session.execute(query, (row.id, chunk_id, row.title, row.description,row.link,row.imagelink,row.availability,  pricevalue ,row.brand,row.condition,row.producttype,row.sale_price, embeddings))