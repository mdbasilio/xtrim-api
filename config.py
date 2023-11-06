class Config:
    SECRET_KEY = '1233'


class DevelomentConfig(Config):
    DEBUG = True
    # Configuración BD
    MYSQL_HOST = '127.0.0.1'
    MYSQL_USER = 'devpy'
    MYSQL_PASSWORD = 'P@s5word*123'
    MYSQL_DB = 'db_appxtrim'

    # Rutas de los directorios de imágenes
    RUTA_PLANES = 'RUTA_PLANES'
    RUTA_PROMO = 'RUTA_PROMO'
    RUTA_SEGURIDAD = 'RUTA_SEGURIDAD'

class ProductionConfig(Config):
    DEBUG = True
    # Configuración BD
    MYSQL_HOST = '192.168.21.18'
    MYSQL_USER = 'usr_ecomerce'
    MYSQL_PASSWORD = 'usr_ecomerce'
    MYSQL_DB = 'ecomerce'

    # Rutas de los directorios de imágenes
    RUTA_PLANES = 'RUTA_PLANES'
    RUTA_PROMO = 'RUTA_PROMO'
    RUTA_SEGURIDAD = 'RUTA_SEGURIDAD'

config = {
    'development' : DevelomentConfig,
    'prod' : ProductionConfig
}