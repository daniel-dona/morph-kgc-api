from flask import Flask, render_template, request, send_file
from flask_cors import CORS
import morph_kgc
import zipfile
import traceback

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = "/data/"

pathFiles = "/data/"
pathZipFile = pathFiles + "csv.zip"
pathRmlMapping = pathFiles + "mapping.ttl"
outputPathFile = "/output/result.ttl"
outputPathZippedFile = "/output/result.zip"

def run_morph_kgc():
	
	config = '''
	[CONFIGURATION]

	# INPUT
	na_values=,#N/A,N/A,#N/A N/A,n/a,NA,,#NA,NULL,null,NaN,nan

	[KNOWLEDGEGRAPH]
	source_type: csv
	mappings:/data/mapping.ttl
	
	'''
	
	graph = morph_kgc.materialize(config)
	graph.serialize(destination=outputPathFile, format='turtle')

def compress_result():
	zipObj = zipfile.ZipFile(outputPathZippedFile, 'w')
	zipObj.write(outputPathFile, "result.ttl")
	zipObj.close()

@app.route('/', methods = ['POST',"GET"])
def upload_file():
	try:
		if request.method == 'POST':
			mapping = request.form['mapping']
			
			print(mapping)
			
			f = open(pathRmlMapping, 'w')
			f.write(mapping)
			f.close()
			csv = request.files['csv']
			csv.save(pathZipFile)
			with zipfile.ZipFile(pathZipFile, 'r') as zip_ref:
			   zip_ref.extractall(pathFiles)
			   
			   
			run_morph_kgc()
			compress_result()
			return send_file(outputPathZippedFile, mimetype='application/x-zip')
		elif request.method == "GET":
			return 'Hello World!'
	except Exception as e:
		print(traceback.format_exc())
		return "Error..."

if __name__ == '__main__':
   app.run(host="0.0.0.0", port="5000",debug= True)
