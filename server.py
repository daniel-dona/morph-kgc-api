from flask import Flask, send_file, jsonify
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from flask_restful import Resource, Api, reqparse
from werkzeug import datastructures
import tempfile
from flask_cors import CORS
import morph_kgc
import zipfile
import traceback
import rdflib
import io
import os

parser = reqparse.RequestParser()
parser.add_argument('mapping',type=datastructures.FileStorage, location='files')
parser.add_argument('data',type=datastructures.FileStorage, location='files')

app = Flask(__name__)
api = Api(app)
CORS(app)

SWAGGER_URL = '/docs' 
API_URL = '/'

old = []

swaggerui_blueprint = get_swaggerui_blueprint(
	SWAGGER_URL,  
	API_URL,
	config={ 
		'app_name': "Morph-KGC API"
	},
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def purge_mapping(mapping_path, data_path):
	
	try:
	
		g = rdflib.Graph().parse(mapping_path, format="turtle")
		
		for t in g:
			
			if t[1] ==  rdflib.term.URIRef('http://semweb.mmlab.be/ns/rml#source'):
				
				new = (t[0], t[1], rdflib.term.Literal(data_path+str(t[2]).replace("/data/", "")))
				
				g.remove(t)
				g.add(new)
				
				#print("Removed:", t)
				#print("Added:", new)

		
		g.serialize(destination=mapping_path, format='nt', encoding="utf-8")
		
	except:
		
		print("Unable to parse mapping!")

def run_morph_kgc(mapping_path, output_path):
	
	#data_path = 
	
	config = '''
	[CONFIGURATION]

	# INPUT
	na_values=,#N/A,N/A,#N/A N/A,n/a,NA,,#NA,NULL,null,NaN,nan

	[KNOWLEDGEGRAPH]
	mappings:'''+mapping_path
	
	graph = morph_kgc.materialize(config)
	graph.serialize(destination=output_path, format='nt',  encoding="utf-8")


class Server(Resource):
	
	def get(self):
		 
		swag = swagger(app)
		swag['info']['version'] = "1.5.0"
		swag['info']['title'] = "Morph-KGC API"
		
		
		
		return jsonify(swag)

	def post(self):
		
		with tempfile.TemporaryDirectory(prefix="morph-kgc") as run_dir:
		
			data_dir = run_dir+"/data/"
			
			#mapping_file = tempfile.NamedTemporaryFile(prefix="morph-kgc_mapping", suffix=".ttl", dir=run_dir).name
			#data_file = tempfile.NamedTemporaryFile(prefix="morph-kgc_data", suffix=".zip", dir=run_dir).name
			
			mapping_file = run_dir+"/mapping.ttl"
			data_file_zip = run_dir+"/data.zip"
			output_file = run_dir+"/result.nt"
			output_file_compressed = run_dir+"/result.zip" #io.BytesIO()
			
			data = parser.parse_args()
			
			if data['mapping'] != None and data['data'] != None:
				
				os.mkdir(data_dir)
				
				data['mapping'].save(mapping_file)
				
				print(data['data'])
				
				if data['data'].mimetype == 'application/zip':
					
					data['data'].save(data_file_zip)
				
					with zipfile.ZipFile(data_file_zip, 'r') as zip_data:
						
						print(zip_data.infolist())
						zip_data.extractall(path=data_dir)
						
				elif data['data'].mimetype == "text/csv" or data['data'].mimetype == "application/json" or data['data'].mimetype == "text/xml":
					
					data['data'].save(data_dir+data['data'].filename)
					
				else:
					
					return ("Not supported data file, check contents or extension!", 400)
					
				
				try:
				
					purge_mapping(mapping_file, data_dir)
					
				except: 
					
					return ("There is an error with your mapping!", 400)
				
				try:
				
					run_morph_kgc(mapping_file, output_file)
					
				except:
					
					return ("Materialization failed!", 400)
				
				zipObj = zipfile.ZipFile(output_file_compressed, 'w')
				zipObj.write(output_file, "result.nt")
				zipObj.close()
				
				#output_file_compressed.seek(0)
				
				return send_file(output_file_compressed, mimetype='application/x-zip')
			
			else:
				
				print("Not valid request")
			
				print(data)
				
				abort(400)

api.add_resource(Server, API_URL)


def run(host="0.0.0.0", port=5000):
	
	print("API URL: "+API_URL)
	print("SWAGGER URL: "+SWAGGER_URL)
	
	app.run(debug=False, host=host, port=port)

if __name__ == '__main__':
	run()
