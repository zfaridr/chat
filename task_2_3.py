import yaml

data = {'stuff': ['table', 'sofa', 'cupboard', 'window', 'chair'],
           'stuff_amount': 4,
           'stuff_ptice': {'table': '100\u00a5-1000\u00a5',
                           'sofa': '1000\u20ac-3000\u20ac',
                           'cupboard': '500\u20ac-100\u20ac',
                           'window': '200\u20ac-400\u20ac',
                           'chair': '100\u00a5-200\u00a5'}
        }

with open('data.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open("data.yaml", 'r', encoding='utf-8') as f:
    data_2 = yaml.load(f, Loader=yaml.SafeLoader)

print(data == data_2)