import re
import pandas as pd
from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
from flask import Response
import sqlite3 as sql

app = Flask(__name__)
app.json_encoder = LazyJSONEncoder
swagger_template = {
    'swagger': '2.0',
    'info' : {
        'title' :  'API Documentation for Data Processing and Modeling',
        'description' : 'Dokumentasi API untuk processing dan modelling data teks untuk membersihkan kata-kata Hate Speech dan Abusive',
        'version' : '1.0.0'
        
    }

}
swagger_config = {
    'headers' : [],
    'specs' : [
        {
            'endpoint' : 'docs',
            'route' : '/docs.json'
        }
    ],
    'static_url_path' :'/flasgger_statis',
    'swagger_ui' :True,
    'specs_route' : '/docs/' 

}
@app.route('/')
def welcoming():
    return 'Welcome to my API'

swagger = Swagger(app, config=swagger_config,template=swagger_template)
@swag_from('docs/text-implementing.yml', methods=['POST'])
@app.route('/text-implementing', methods=['POST'])
def text_implementing ():
    inputing_text = request.form.get('text')
    outputing_text = cleansing(inputing_text)

    json_respon = {
        'input' : inputing_text,
        'output' :outputing_text
    }

    result_response = jsonify(json_respon)

    return result_response

@swag_from ('docs/file-uploading.yml', methods=['POST'])
@app.route ('/file-uploading', methods=['POST'])
def uploading_file():
    global connection_data  #

    files = request.files['file']
    if not files:
        return jsonify({'error': 'No file provided'}), 400

    try:
        data_csv = pd.read_csv(files, encoding="latin-1")
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'Empty CSV file'}), 400

    data_csv = data_csv['Tweet']
    data_csv = data_csv.drop_duplicates()
    
    data_csv = data_csv.values.tolist()
    file_data = {}
    x = 0

    for string in data_csv:
        file_data[x] = {}
        file_data[x]['tweet'] = string
        file_data[x]['new_tweet'] = cleansing(string)
        x += 1
    # Membuat DataFrame dari hasil cleaning data
    result_df = pd.DataFrame(file_data).T

    # M
    result_csv = result_df.to_csv(index=False)

    response = Response(
        result_csv,
        content_type='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=result.csv'
        }
    )

    return response

connection_data = sql.connect("abusive_text.db", check_same_thread=False)

def sensoring_text(str):
    df_abusive = pd.read_sql_query("select * from ABUSIVE", connection_data)
    dict_abusive = dict(zip(df_abusive['teks'], df_abusive['teks']))
    for x in dict_abusive:
        str = str.replace(x, '*' * len(x))  
    return str
def preprocessing_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z]', ' ', text)
    text = text.replace('user', '')
    words = [word for word in text.split() if len(word) > 2]
    return ' '.join(words)

def normalize_text(text):
    data_alay = pd.read_sql_query('select * from ALAY', connection_data)
    dict_alay = dict(zip(data_alay['teks_alay'], data_alay['teks_baku'])) #Membungkus data teks_alay dan teks baku menjadi dictionary
    text_list = text.split()
    
    text_normal_list = [dict_alay.get(word, word) for word in text_list] #Mengambil nilai baku pada data teks_baku
    
    text_normal = ' '.join(text_normal_list) #mengganti teks yang tidak baku menjadi baku
    return text_normal.strip()

def normalization_abusive(teks):
    df_abusive = pd.read_sql_query("select * from ABUSIVE", connection_data)
    dict_abusive = dict(zip(df_abusive['teks'],df_abusive['teks']))
    teks = teks.split()
    teks_normal = ''
    for str in teks:
        if(bool(str in dict_abusive)):
            str = sensoring_text(str)
            teks_normal = teks_normal + ' ' + str
        else:
            teks_normal = teks_normal + ' ' + str  
    teks_normal = teks_normal.strip()
    return teks_normal

def cleansing (text):
    text = preprocessing_text(text)
    text = normalize_text (text)
    text = normalization_abusive(text)
    
    return text

if __name__ == '__main__' :
    app.run(debug=True)
