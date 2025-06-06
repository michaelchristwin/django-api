import requests, base64, binascii, regen_pb2, json, os

from urllib.request import urlopen
from dune_client.client import DuneClient

from .models import ProjectMetric


def update(pk, value):
    metric = ProjectMetric.objects.get(db_id=pk)
    metric.value = value
    metric.save()


def get_baserow_data(table_id, params):
    url = baserow_api + table_id + "/?user_field_names=true&" + params
    headers = {'Authorization': baserow_token, 'Content-Type' : 'application/json'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200: return response.json()
    else: raise Exception(f"Failed to fetch Baserow data with status {response.status_code}. {response.text}")


def load_dune(impact):
    for metric in impact['metrics']:
        query = dune.get_latest_result(metric['query'], max_age_hours=int(metric['max_age']))
        value = round(float(query.result.rows[int(metric['result_index'])][metric['result_key']]), 2)
        if metric['denominator'] is not None: value = value / int(metric['denominator'])
        update(metric['db_id'], value)


def load_client(impact):
    if impact['method'] == "POST":
        post_body_json = json.dumps(impact['body'])
        post_body = json.loads(post_body_json)
        response = requests.post(impact['api'], json=post_body)
        metric_data = response.json()[impact['result_key']][impact['result_index']]

        for metric in impact['metrics']:
            value = metric_data[metric['result_key']]
            formatted_value = round(float(value) / impact['global_denominator'], 2) if impact['global_operator'] == "divide" else round(float(value), 2)
            if metric['operator'] == "multiply": formatted_value = round(formatted_value * metric['denominator'], 2)
            if metric['operator'] == "divide": formatted_value = round(formatted_value / metric['denominator'], 2)
            update(metric['db_id'], formatted_value)

    if impact['method'] == "GET":
        if impact['result_key'] is not None:
            response = requests.get(impact['api'])
            for metric in impact['metrics']:
                value_path = impact['result_key'] + "." + metric['result_key']
                value = round(float(utils.get_nested_value(response.json(), value_path)), 2)
                if metric['denominator'] is not None: value = value / int(metric['denominator'])
                update(metric['db_id'], value)
        else:
            for metric in impact['metrics']:
                list_value = 0
                api = impact['api'] + metric['query']
                response = requests.get(api)                           
                value = response.json()
        
                if type(value) == int: 
                    if metric['denominator'] is not None: value = float(response.json() / int(metric['denominator']))
                if type(value) == dict:
                    if 'list_name' in metric:
                        for i in value[metric['list_name']]: list_value += float(i[metric['result_key']])
                        value = list_value
                    else: value = float(value[metric['result_key']])
                    if metric['denominator'] is not None: value = value / int(metric['denominator'])
                update(metric['db_id'], round(value, 2))


def load_subgraph(impact):
    for metric in impact['metrics']:
        cumulative_value = 0
        for q in metric['query']:
            response = requests.post(impact['api'].replace('{api_key}', os.getenv('SUBGRAPH_API_KEY')) + q, json={'query': metric["graphql"]})
            if response.status_code == 200:
                result = response.json()['data'][impact['result_key']]
                for r in result: 
                    if r['key'] == metric['result_key']: cumulative_value += float(r['value'])
        update(metric['db_id'], cumulative_value)



def load_graphgl(impact):
    result_list = []

    if impact['query'] is not None and len(impact['query']) > 0:
        for q in impact['query']:
            gql_query = impact['graphql'].replace('{query}', '"' + q + '"')
            response = requests.post(impact['api'], json={'query': gql_query})

            if response.status_code == 200:
                result = response.json()['data'][impact['result_key']][impact['result_index']]
                result_list.append(result)

                for metric in impact['metrics']:
                    metric_name = metric['db_id']
                    cumulative_value = 0
                            
                    for r in result_list: 
                        if metric['result_key'] in r: cumulative_value += float(r[metric['result_key']])
                    update(metric['db_id'], cumulative_value)

    else:
        response = requests.post(impact['api'], json={'query': impact['graphql'], "variables": impact['variables']})
        if response.status_code == 200:
            if impact['result_index'] is not None: result = response.json()['data'][impact['result_key']][impact['result_index']]
            else: result = response.json()['data'][impact['result_key']]
            result_list.append(result)

            for metric in impact['metrics']:
                for r in result_list: 
                    if metric['result_key'] in r: value = float(r[metric['result_key']])
                if metric['operator'] == "divide": value = value / metric['denominator']
                update(metric['db_id'], value)


def load_regen(impact):
    denom_list = []
    hex_denom_list = []
    cumulative_retired_amount = 0
    bridged_amount = 0
    onchain_issued_amount = 0

    row = requests.post(
        impact['api'],
        headers={'Content-Type': 'application/json'},
        json={
            'jsonrpc':'2.0',
            'id':176347957138,
            'method':'abci_query',
            'params':{
                'path':'/regen.ecocredit.v1.Query/Batches',
                'prove':False
                }
        }
    )

    value = row.json()['result']['response']['value']
    decoded_bytes = base64.b64decode(value)

    message = regen_pb2.QueryBatchesResponse()
    message.ParseFromString(decoded_bytes)

    for batch in message.batches:
        denom_list.append(batch.denom)

    for denom in denom_list:
        byte_denom = denom.encode("utf-8")
        length_hex = hex(len(denom))[2:].zfill(2)
        prefix = "0a" + length_hex
        hex_denom = prefix + binascii.hexlify(byte_denom).decode('utf-8')
        hex_denom_list.append({"hex": hex_denom, "string": denom})

    for item in hex_denom_list:
        result = requests.post(
            impact['api'],
            headers={'Content-Type': 'application/json'},
            json={
                'jsonrpc':'2.0',
                'id':717212259568,
                'method':'abci_query',
                'params':{
                    'path':'/regen.ecocredit.v1.Query/Supply',
                    'data': item['hex'],
                    'prove':False
                }
            }
        )

        value = result.json()['result']['response']['value']
        decoded_bytes = base64.b64decode(value)

        message = regen_pb2.QuerySupplyResponse()
        message.ParseFromString(decoded_bytes)

        cumulative_retired_amount += float(message.retired_amount)
        credit_class = item['string'].split("-")[0]

        if credit_class != "KSH01" and credit_class != "C03": bridged_amount += float(message.retired_amount) + float(message.tradable_amount)
        if credit_class == "KSH01" or credit_class == "USS01": onchain_issued_amount += float(message.retired_amount) + float(message.tradable_amount)

    for metric in impact['metrics']:
        if metric['result_key'] == "cumulative_retired_amount": value = cumulative_retired_amount
        if metric['result_key'] == "bridged_amount": value = bridged_amount
        if metric['result_key'] == "onchain_issued_amount": value = onchain_issued_amount                
        update(metric['db_id'], round(value, 2))



def load_near(impact):
    cumulative_value = 0
    post_body_json = json.dumps(impact['body'])
    post_body = json.loads(json.dumps(impact['body']))
    response = requests.post(impact['api'], headers={'Content-Type': 'application/json'}, json=post_body)
    result = response.json()[impact['result_key']][impact['result_index']]
    decoded_response = ''.join([chr(value) for value in result])
    data = json.loads(decoded_response)

    for metric in impact['metrics']:
        for item in data:
            value = float(item[metric['result_key']])
            if metric['denominator'] is not None: value = value / int(metric['denominator'])
            if metric['type'] == "cumulative": cumulative_value += value
    update(metric['db_id'], round(cumulative_value, 2))



def load():
    # Dune initialization
    dune = DuneClient(os.getenv('DUNE_KEY'))
    impact_data = get_baserow_data('171320', "filter__field_2405062__not_empty&include=Impact Metrics JSON")
    for json_file in impact_data['results']:
        json_url = json_file['Impact Metrics JSON'][0]['url']
        response = urlopen(json_file['Impact Metrics JSON'][0]['url'])
        data = json.loads(response.read())

        for impact in data['impact_data']:
            if impact['source'] == "dune": load_dune(impact)
            if impact['source'] == "client": load_client(impact)
            if impact['source'] == "subgraph": load_subgraph(impact)
            if impact['source'] == "graphql": load_graphql(impact)
            if impact['source'] == "regen": load_regen(impact)
            if impact['source'] == "near": load_near(impact)
