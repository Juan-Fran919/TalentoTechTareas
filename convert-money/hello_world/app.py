import json

# import requests


def lambda_handler(event, context):
    tipo_moneda = event["queryStringParameters"]["moneda"]
    cantidad = event["queryStringParameters"]["cantidad"]

    if tipo_moneda == "USD":
        conversion = float(cantidad) * 18.16
    elif tipo_moneda == "EUR":
        conversion = float(cantidad) * 19.59
    elif tipo_moneda == "MXN":
        conversion = "La vonversion solo es de MXN a otra moneda"
    else:
        conversion = "Moneda no soportada"
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "La conversion es de MXN a" + str(tipo_moneda),
            "Moneda": event["queryStringParameters"]["moneda"],
            "Cantidad": event["queryStringParameters"]["cantidad"],
            "Respuesta": conversion
        }),
    }


