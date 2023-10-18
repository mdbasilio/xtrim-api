from flask import request, jsonify
from flask_mysqldb import MySQL
from flask_openapi3 import OpenAPI, Info, Tag
import requests
from pydantic import BaseModel, Field
from config import config
import os
import base64
import logging
from werkzeug.utils import secure_filename

# Configuración de logs
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_filename = 'record.log'

logging.basicConfig(filename=log_filename, level=logging.DEBUG, format=log_format)


#Instancia
app_config = config['development']  

info = Info(title="API XTRIMIR", version="1.0.0")
app = OpenAPI(__name__, info=info)

app.config['MYSQL_HOST'] = app_config.MYSQL_HOST
app.config['MYSQL_USER'] = app_config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = app_config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = app_config.MYSQL_DB

db = MySQL(app)

@app.route('/')
def Index():
    return 'Inicio Api Xtrim'

def get_roles_from_db():
    sql = "SELECT * FROM db_appxtrim.roles"
    cursor = db.connection.cursor()
    cursor.execute(sql)
    column_names = [desc[0] for desc in cursor.description]
    roles = [dict(zip(column_names, row)) for row in cursor.fetchall()]  
    return roles

rol_tag = Tag(name="Roles", description="Administración de Roles")

class RoleModel(BaseModel):
    idroles: int
    estado: str
    negocio: str
    miscuentas: int
    resumen: int
    mejorarplan: int
    competatuexperiencia: int
    revisionservicio: int
    turnos: int

class RolesResponse(BaseModel):
    code: int = Field(0, description="Código de estado")
    message: str = Field("OK", description="Mensaje de respuesta")
    data: RoleModel

@app.get("/get_roles", summary="Lista todos los roles", tags=[rol_tag],
         responses = {
            200: RolesResponse,
            422: None           
         })
def get_roles():
    try:
        app.logger.debug("Inicio get_roles")
        roles = get_roles_from_db()
        app.logger.info("Roles obtenidos exitosamente")
        return {"code": 200, "message": "OK", "data": roles}
    except Exception as e:
        app.logger.error(f"Error al obtener roles: {str(e)}")
        return {"code": 500, "message": "Error al obtener roles", "data": []}
    finally:
        app.logger.debug("Fin get_roles")



def obtener_rutas_por_prefijo(prefijo):
    try:
        cursor = db.connection.cursor()

        cursor.callproc("consultar_registros_por_prefijo", (prefijo,))
        records = cursor.fetchall()

        carpetas = [record[2] for record in records]

        return carpetas
    finally:
        cursor.close()


def convertir_imagen_a_base64(imagen_path):
    with open(imagen_path, 'rb') as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
    return img_base64

img_tag = Tag(name="Imagenes", description="Imagenes de banners")

class ImgQuery(BaseModel):
    type: int = Field(..., description='Tipo', example=1)

class ImgModel(BaseModel):
    nombre: str
    url_b64: str

class RolesResponse(BaseModel):
    code: int = Field(0, description="Código de estado")
    message: str = Field("OK", description="Mensaje de respuesta")
    data: ImgModel

@app.get('/get_imagenes', summary="Lista de imagenes", tags=[img_tag],
         responses = {
            200: RolesResponse,
            422: None           
         })
def get_imagenes(query: ImgQuery):
    try:
        app.logger.debug("Inicio get_imagenes")

        carpetas = obtener_rutas_por_prefijo('RUTA_PLANES')
        logging.info(f"Carpetas {carpetas}")

        img_data_list = []
        index = 0

        for carpeta in carpetas:
            index += 1

            img_list = [f for f in os.listdir(carpeta) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            logging.info(f"Imagenes {img_list}")

            for img_filename in img_list:
                img_path = os.path.join(carpeta, img_filename)
                logging.info(f"Imagen Individual {img_path}")

                nombre_archivo, extension = os.path.splitext(img_filename)
                
                with open(img_path, 'rb') as img_file:
                        img_data = img_file.read()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        logging.info(f"Imagen base64 {img_base64}")
                    
                        img_data_list.append({
                                'nombre': nombre_archivo,
                                'img_base64': img_base64,
                                'tipoImg': index
                            })


        return jsonify({"code": 200, "message": "OK", "data": img_data_list})


        #return jsonify({"code": 200, "message": "OK", "data": carpetas})
    except Exception as e:
        # Manejo de errores generales
        return jsonify({"code": 500, "message": "Internal Server Error", "data": str(e)})
    finally:
        app.logger.debug("Fin get_imagenes")


ALLOWED_URL_PREFIX = "http"

@app.route('/descargar_archivo', methods=['POST'])
def descargar_archivo():
    # Obtén la ruta del archivo PDF desde la solicitud POST
    pdf_path = request.json.get('ruta')

    if not pdf_path:
        return jsonify({"error": "La ruta del PDF no se proporcionó en el cuerpo de la solicitud."}), 400

    logging.info('Solicitud de descarga de PDF - Ruta del archivo: %s', pdf_path)

    try:
        # Verificar si la ruta es una URL (comienza con "http")
        if pdf_path.startswith(ALLOWED_URL_PREFIX):
            response = requests.get(pdf_path)
            if response.status_code == 200:
                pdf_base64 = base64.b64encode(response.content).decode('utf-8')
                return jsonify({"pdf_base64": pdf_base64}), 200
            else:
                return jsonify({"error": "No se pudo obtener el archivo PDF de la URL proporcionada."}), 404
        else:
            # Verifica si el archivo PDF existe en la ruta compartida
            if not os.path.exists(pdf_path):
                return jsonify({"error": "El archivo PDF no se encuentra en la ruta especificada."}), 404

            # Abre el archivo PDF y lo convierte en una cadena Base64
            with open(pdf_path, 'rb') as pdf_file:
                pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

            return jsonify({"pdf_base64": pdf_base64}), 200

    except Exception as e:
        logging.error('Solicitud de carga de archivos - Error: %s', str(e))
        return jsonify({"error": f"Se produjo un error al convertir el PDF a Base64: {str(e)}"}), 500
    finally:
        logging.info("Fin descargar_archivo")

# Establece la carpeta de destino para la subida de archivos
UPLOAD_FOLDER = 'static/uploads' # Carpeta de destino por defecto
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['pdf', 'doc', 'jpg', 'png'])

# Función para verificar si la extensión de un archivo es válida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 

@app.route('/subir_archivos', methods=['POST'])
def upload_file():
    try:
        ruta_destino = request.form.get('ruta')  # Obtiene la ruta de destino del cuerpo del request

        if not ruta_destino:
            resp = jsonify({'message': 'No se especificó una ruta de destino en la solicitud'})
            resp.status_code = 400
            return resp

        cedula = request.form.get('cedula')  # Obtiene el número de cédula del cuerpo del request

        if not cedula:
            resp = jsonify({'message': 'No se especificó un número de cédula en la solicitud'})
            resp.status_code = 400
            return resp

        # Enmascarar el número de cédula en los registros
        cedula_enmascarada = cedula[:4] + '*****' + cedula[-2:]

        files = request.files.getlist('archivos')
        if 'archivos' not in request.files:
            resp = jsonify({'message': 'No se seleccionaron archivos'})
            resp.status_code = 400
            return resp

        # Registrar la información con la cédula enmascarada
        logging.info('Solicitud de carga de archivos - Ruta de destino: %s, Numero de cedula: %s', ruta_destino, cedula_enmascarada)

        # Obtener la lista de archivos en el directorio de subida
        existing_files = os.listdir(ruta_destino)

        # Contar la cantidad de archivos existentes con el mismo número de cédula
        num_existing_files = sum(1 for filename in existing_files if filename.startswith(f'{cedula}V'))

        errors = {}
        success = False

        for i, file in enumerate(files, start=num_existing_files + 1):
            if file:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    nuevo_nombre = f'{cedula}V{i}.{filename.split(".")[-1]}'
                    file.save(os.path.join(ruta_destino, nuevo_nombre))
                    success = True
                else:
                    errors[file.filename] = 'Tipo de archivo no permitido'
            else:
                errors['message'] = 'No se seleccionaron archivos'

        if success and errors:
            errors['message'] = 'Algunos archivos se subieron con éxito, pero otros no se permitieron'
            resp = jsonify(errors)
            resp.status_code = 500
            return resp
        if success:
            resp = jsonify({'message': 'Archivos subidos con éxito'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify(errors)
            resp.status_code = 500
            return resp

    except Exception as e:
        logging.error('Solicitud de carga de archivos - Error: %s', str(e))
        return jsonify({'message': 'Ocurrió un error al procesar la solicitud'}), 500
    finally:
        logging.info("Fin upload_file")



if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run(debug=True)
 