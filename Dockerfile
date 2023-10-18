# Usa una imagen base de Python
FROM ubuntu

RUN apt update
RUN apt install python3-pip -y

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de la aplicación al contenedor
COPY . /app

# Instala las dependencias de la aplicación
RUN pip3 install -r requirements.txt

# Expone el puerto en el que se ejecuta la aplicación Flask
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
