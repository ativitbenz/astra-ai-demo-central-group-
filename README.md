# astra-ai-demo

# Multilingual Text Similarity with Vector Search

Demonstrate Datastax [Astra's](https://docs.datastax.com/en/astra-serverless/docs/vector-search/overview.html) Vector search with Text similarity search using Retail eCommerce product Dataset

# Demo UI

[demoui.jpg]


Some guidance below on how you can learn to do text similarity with Vector search

This repository includes 2 sections 

1. Backend
- Generate Vector embeddings for product dataset in language other than english
- Load Vector embeddings into Astra
- Exposes an API to perform Vector search and retrieve similar products
2. Frontend
- Chat GPT like interface built in react to search items by context for similar items

## 1. Backend

The [loadDataEmbed.py] python code creates the embeddings using a Multilingual model and stores in Astra VectorDB. Refer to [Cohere Multi Lingual Model](https://docs.cohere.com/docs/multilingual-language-models) for how to generate embeddings for text in other language other than English. The dimensions of the multilingual embeddings is 768 dimensions.

The code also creates required tables and the indexes in Astra

The sample Dataset includes `52,000` products.

#### Setup to run the backend

Review the Astra [Getting started](https://docs.datastax.com/en/astra-serverless/docs/getting-started/getting-started.html) guide, if needed.

Create a new vector search enabled database in Astra. astra.datastax.com

For the easy path, name the keyspace in that database with the name, as required.

Create a token with permissions to create tables
Download your secure-connect-bundle zip file.
Set up an open.ai API account and generate a key
Set up an cohere API account and generate a key
Create an .env file with the below keys and update the Environment Variables cell

```
    openai_api_key = "<open api key>"
    cass_user = '<client id from the astra token>'
    cass_pw = '<client password from the astra token>'
    scb_path = '<path to secure connect bundle>'x`
    keyspace='<your keyspace>'
    table='<your table>'
    data_file='<your dataset>'
    coherekey='<cohere key>'

```
If you are changing your dataset review the below code to create the table and indexes and modify the columns appopriately


```
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
```

Run the below command to generate embeddings and load data


```
python3 loadDataEmbed.py
```

#### Generate Vector embedding and Load data

Run the below command and it should pick up the dataset in csv file ,create table, generate embeddings for the product description and price in the dataset and store in AstraDB


```
python3 similaritysearch.py
```

## Similarity Search API

The API in [similaritysearch.py] queries that table and uses the results to give ChatGPT some context to support it's response. The source sample database is mostly consumer brick and mortar products. 
Here we use the same cohere API that we used to calculate embeddings for each row in the database, but this time we are using your input question to calculate a vector to use in a query. The query vector has the same dimensions (number of entries in the list) as the embeddings we generated for each row in the database. We fetch the top 5 results using ANN Similarity and build a prompt with which we'll query ChatGPT. Note the "roles" in this little conversation give the LLM more context about who that part of the conversation is coming from.

The codes uses a Dataset in thai language. If you prefer to use in other language, modify `Line 112` the below code.

```
thai_response=translator.translate(human_readable_response, dest='th')
```

API Info

Request

```
POST /similaritems
Content-type: application/json

{"newQuestion":"คำแนะนำเกี่ยวกับการออกแบบห้องน้ำหลักใหม่ด้วยสไตล์โมเดิร์นและอุปกรณ์ที่เข้าชุดกัน"}

```

Query
```
SELECT *
    FROM {keyspace}.{table_name}
    ORDER BY openai_description_embedding ANN OF {embeddings} LIMIT 5"
```

---

## Frontend

In `App.js`

Replace `Line 38` with your API Server URL

```
const response = await axios.post('http://localhost:9000/similaritems', { newQuestion });
```
For the first time

```
npm install
```

and start the frontent app using

```
npm start
```
--- 

# Credits And References

The react app was generated using [Create React App](https://create-react-app.dev/)

The Chat GPT clone was built by with this [reference](https://kinsta.com/blog/chatgpt-clone/)

The Multi lingual model code was built using this [reference](https://docs.cohere.com/docs/multilingual-language-models)

The google translation python code was built using this [reference](https://pypi.org/project/googletrans/)

The python backend code was built using this colab notebook from [Kiyu Gabriel](https://github.com/qzg) as [reference](https://colab.research.google.com/drive/1j0PZCwyrs6f560siIabLG0YY2PYWtfpx?usp=sharing#scrollTo=24d02afb-13b1-4c71-8610-90768e21989e)
