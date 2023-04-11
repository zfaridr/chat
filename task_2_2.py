import json


def write_order_to_json(item, quantity, price, buyer, date):
    
    with open('orders.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open('orders.json', 'w', encoding='utf-8', ) as f:
        orders_list = data['orders']
        order = {'item': item, 'quantity': quantity,
                      'price': price, 'buyer': buyer, 'date': date}
        orders_list.append(order)
        json.dump(data, f, indent=4, ensure_ascii=False)


write_order_to_json('laptop', '1', '2000', 'Ivaniv I.I.', '06.04.2023')
write_order_to_json('computer', '2', '4000', 'Petrov P.P.', '07.04.2023')
write_order_to_json('printer', '1', '1000', 'Sidorov S.S.', '07.04.2023')