from ariadne import QueryType, graphql_sync, make_executable_schema
from ariadne.explorer import ExplorerGraphiQL
from flask import Flask, jsonify, request
import requests


'''
type Weather {
    temperature_2m: Float!
    date: Float!
}
'''

type_defs = """
    type Weather {
        city: String!
        date: String!
        min_temp: Float!
        max_temp: Float!
        latitude: String!
        longitude: String!
    }
    
    type Restaurant {
        name: String!
        addr_street: String
        addr_city: String
        website: String
    }

    type Query {
        getRestaurant(city: String!): [Restaurant!]
        getWeather(city: String!, date: String!): Weather!
    }
"""

query = QueryType()


@query.field("getWeather")
def resolve_getWeather(_, info, city, date):
    response = requests.get(f"http://127.0.0.1:5000/api/v1/ciudad/{city}/clima/{date}")
    if response.status_code == 200:
        weather_data = response.json()
        return weather_data
    else:
        return None


@query.field("getRestaurant")
def resolve_getRestaurant(_, info, city):
    response = requests.get(f"http://127.0.0.1:5000/api/v1/ciudad/{city}/restaurantes")
    if response.status_code == 200:
        restaurant_data = response.json()
        return restaurant_data
    else:
        return None

schema = make_executable_schema(type_defs, query)

app = Flask(__name__)

# Retrieve HTML for the GraphiQL.
# If explorer implements logic dependant on current request,
# change the html(None) call to the html(request)
# and move this line to the graphql_explorer function.
explorer_html = ExplorerGraphiQL().html(None)


@app.route("/graphql", methods=["GET"])
def graphql_explorer():
    # On GET request serve the GraphQL explorer.
    # You don't have to provide the explorer if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL explorer app.
    return explorer_html, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    # GraphQL queries are always sent as POST
    data = request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(debug=True, port=5001)
