import json
import boto3
import uuid
from datetime import datetime
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event['path']

        if http_method == 'PUT' and path == '/CrearProducto':
            return crear_producto(event)
        elif http_method == 'GET' and path == '/ListarProductos':
            return listar_productos()
        elif http_method == 'GET' and path.startswith('/DetalleProducto/'):
            return detalle_producto(event)
        elif http_method == 'PUT' and path.startswith('/EditarProducto/'):
            return editar_producto(event)
        elif http_method == 'DELETE' and path.startswith('/EliminarProducto/'):
            return eliminar_producto(event)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Ruta o método no soportado'})
            }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error en el servidor',
                'error': str(e)
            })
        }

def validar_parametros(params, required_params):
    missing_params = [param for param in required_params if param not in params]
    if missing_params:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Faltan parámetros necesarios: {", ".join(missing_params)}'})
        }
    return None

def crear_producto(event):
    try:
        # Extraer los parámetros de la consulta
        # params = event['queryStringParameters']
        params = event.get('queryStringParameters', {})
        validacion = validar_parametros(params, ['nombre', 'descripcion', 'precio'])
        if validacion:
            return validacion
        
        # Crear un ID único para el producto
        product_id = str(uuid.uuid4())
        creation_date = datetime.utcnow().isoformat()
        
        # Crear el elemento que se almacenará en DynamoDB
        item = {
            'id': product_id,
            'fecha_creacion': creation_date,
            'nombre': params['nombre'],
            'descripcion': params['descripcion'],
            'precio': Decimal(params['precio'])
        }
        
        # Guardar el elemento en la tabla DynamoDB
        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Producto creado exitosamente',
                'product_id': product_id
            })
        }
    
    except Exception as e:
        print(f"Error en crear producto: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al crear el producto',
                'error': str(e)
            })
        }

def listar_productos():
    try:
        response = table.scan()
        items = response.get('Items', [])
        items.sort(key=lambda x: x['fecha_creacion'], reverse=True)

        return {
            'statusCode': 200,
            'body': json.dumps(items, default=str)
        }
        
    except Exception as e:
        print(f"Error en listar productos: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al listar los productos',
                'error': str(e)
            })
        }

def detalle_producto(event):
    try:
        path_parameters = event.get('pathParameters', {})
        product_id = path_parameters.get('id')

        response = table.query(
            KeyConditionExpression=Key('id').eq(product_id)
        )
        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Producto no encontrado'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps(items[0], default=str)
        }
    
    except Exception as e:
        print(f"Error en detalle producto: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al obtener el producto',
                'error': str(e)
            })
        }

def editar_producto(event):
    try:
        path_parameters = event.get('pathParameters', {})
        product_id = path_parameters.get('id')
        params = event.get('queryStringParameters', {})

        if not params:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Faltan parámetros necesarios'})
            }

        response = table.query(
            KeyConditionExpression=Key('id').eq(product_id)
        )
        items = response.get('Items', [])
        if not items:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Producto no encontrado'})
            }
        
        update_expression = 'SET '
        expression_attribute_values = {}
        for key, value in params.items():
            update_expression += f'{key} = :{key}, '
            expression_attribute_values[f':{key}'] = value
        
        update_expression = update_expression[:-2]

        expression_attribute_values[':fecha_edicion'] = datetime.utcnow().isoformat()
        update_expression += ', fecha_edicion = :fecha_edicion'

        # Actualizar el producto en la tabla DynamoDB
        response = table.update_item(
            Key={'id': product_id, 'fecha_creacion': items[0]['fecha_creacion']},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        response = {
            'statusCode': 200,
            'body': json.dumps(response['Attributes'], default=str)
        }
        
        return response
        
    except Exception as e:
        print(f"Error en editar producto: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al editar el producto',
                'error': str(e)
            })
        }
    
def eliminar_producto(event):
    try:
        path_parameters = event.get('pathParameters', {})
        product_id = path_parameters.get('id')

        response = table.query(
            KeyConditionExpression=Key('id').eq(product_id)
        )
        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Producto no encontrado'})
            }
        
        table.delete_item(
            Key={'id': product_id, 'fecha_creacion': items[0]['fecha_creacion']}
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Producto eliminado exitosamente'})
        }
        
    except Exception as e:
        print(f"Error en eliminar producto: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al eliminar el producto',
                'error': str(e)
            })
        }
