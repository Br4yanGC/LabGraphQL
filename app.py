from flask import Flask, request, jsonify
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'Hi!'

# Ruta para buscar la ubicación de una ciudad en la API de Nominatim
@app.route('/search_city')
def search_city():
  # Obtén el valor del parámetro 'city' de la URL
  city = request.args.get('city')

  # Verifica si se proporcionó el parámetro 'city'
  if not city:
    return jsonify({'error': 'El parámetro "city" es obligatorio'}), 400

  # URL de la API de Nominatim
  api_url = 'https://nominatim.openstreetmap.org/search'

  # Parámetros de la solicitud
  params = {
    'q': city,
    'format': 'json'
  }

  # Realiza la solicitud a la API de Nominatim
  response = requests.get(api_url, params=params)
  # Verifica si la solicitud fue exitosa
  if response.status_code == 200:
    data = response.json()
    result = {
    "latitude": data[0]['lat'],
    "longitude": data[0]['lon']
    }   

    return jsonify(result)
  else:
    return jsonify({'error': 'Error al realizar la solicitud a la API'}), 500

@app.route('/get_temperature', methods=['GET'])
def get_temperature():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    date = request.args.get('date')

    # Perform the internal request to Open Meteo API using latitude and longitude
    open_meteo_url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&start_date={date}&end_date={date}'
    response = requests.get(open_meteo_url)

    if response.status_code == 200:
        data = response.json()
        
        temperatures = data['hourly']['temperature_2m']
        min_temp = min(temperatures)
        max_temp = max(temperatures)

        return jsonify(
            {
                "date": date,
                "min_temp": min_temp, 
                "max_temp": max_temp, 
                "latitude": latitude, 
                "longitude": longitude
            }
        )
    else:
        return jsonify({'error': 'Failed to fetch data from Open Meteo API'}), response.status_code
  
@app.route('/get_restaurants')
def get_restaurants():
  # Obtén las coordenadas de latitud y longitud de los parámetros en la solicitud
  latitude = float(request.args.get('latitude'))
  longitude = float(request.args.get('longitude'))

  # Construir la URL de la API con los valores de latitud y longitud
  url = f"https://api.openstreetmap.org/api/0.6/map?bbox={longitude - 0.01},{latitude - 0.01},{longitude},{latitude}"

  # Realizar la solicitud a la API
  response = requests.get(url)

  # Verificar si la solicitud fue exitosa
  if response.status_code == 200:
    # Parsea el contenido XML de la respuesta
    root = ET.fromstring(response.text)

    # Lista para almacenar los nombres de los restaurantes
    nombres_de_restaurantes = []
    restaurantes = []

    # Itera a través de los elementos "way" en el XML
    for way in root.findall(".//way"):
      amenity_tag = way.find(".//tag[@k='amenity'][@v='restaurant']")
      name_tag = way.find(".//tag[@k='name']")
      
      addr_city = way.find(".//tag[@k='addr:city']")
      addr_street = way.find(".//tag[@k='addr:street']")
      website = way.find(".//tag[@k='website']")
      
      # Filtra los elementos que cumplen con las condiciones minimas: amenity_tag y name_tag 
      if amenity_tag is not None and name_tag is not None:
        nombres_de_restaurantes.append(name_tag.attrib['v'])
        restaurant = {
          "name": name_tag.attrib['v'],
          "addr_city": addr_city.attrib['v'] if addr_city is not None else '',
          "addr_street": addr_street.attrib['v'] if addr_street is not None else '',
          "website": website.attrib['v'] if website is not None else ''
        }
        restaurantes.append(restaurant)


    for node in root.findall(".//node"):
      amenity_tag = node.find(".//tag[@k='amenity'][@v='restaurant']")
      name_tag = node.find(".//tag[@k='name']")

      addr_city = way.find(".//tag[@k='addr:city']")
      addr_street = way.find(".//tag[@k='addr:street']")
      website = way.find(".//tag[@k='website']")

      # Filtra los elementos que cumplen con las condiciones
      if amenity_tag is not None and name_tag is not None:
        nombres_de_restaurantes.append(name_tag.attrib['v'])

        restaurant = {
          "name": name_tag.attrib['v'],
          "addr_city": addr_city.attrib['v'] if addr_city is not None else '',
          "addr_street": addr_street.attrib['v'] if addr_street is not None else '',
          "website": website.attrib['v'] if website is not None else ''
        }
        restaurantes.append(restaurant)
    # Convierte la lista de nombres a formato JSON y devuelve como respuesta
    if nombres_de_restaurantes:
      return jsonify(restaurantes)
    else:
      return "No se encontraron nombres de restaurantes que cumplan con los criterios.", 200

  else:
    return "Error al obtener el mapa geoespacial.", 500

@app.route('/api/v1/ciudad/<string:city_name>/clima/<string:date>', methods=['GET'])
def get_city_weather(city_name, date):
    # Call /search_city to get the latitude and longitude
    response = requests.get(f'http://127.0.0.1:5000/search_city?city={city_name}')

    if response.status_code != 200:
        return jsonify({'error': 'Failed to retrieve city coordinates'}), response.status_code

    city_data = response.json()
    latitude = city_data.get('latitude') 
    longitude = city_data.get('longitude') 

    if (1):
        response2 = requests.get(f'http://127.0.0.1:5000/get_temperature?latitude={latitude}&longitude={longitude}&date={date}')
        weather_data = response2.json()
        weather_data['city'] = city_name
        return jsonify(weather_data)
    else:
        return jsonify({'error': 'Invalid time parameter'}), 400

@app.route('/api/v1/ciudad/<string:city_name>/restaurantes', methods=['GET'])
def get_city_restaurants(city_name):
    # Call /search_city to get the latitude and longitude
    response = requests.get(f'http://127.0.0.1:5000/search_city?city={city_name}')

    if response.status_code != 200:
        return jsonify({'error': 'Failed to retrieve city coordinates'}), response.status_code
    
    city_data = response.json()
    latitude = city_data.get('latitude')  
    longitude = city_data.get('longitude')

    # Call /get_restaurants to get the restaurants associated with latitude and longitude
    response2 = requests.get(f'http://127.0.0.1:5000/get_restaurants?latitude={latitude}&longitude={longitude}')

    if response2.status_code != 200:
        return jsonify({'error': 'Failed to retrieve restaurant data'}), response2.status_code

    if response2.content == b'No se encontraron nombres de restaurantes que cumplan con los criterios.':
        return jsonify({'error': 'No restaurant data found'}), 404

    return jsonify(response2.json())

if __name__ == '__main__':
  app.run(debug=True, port=5000)