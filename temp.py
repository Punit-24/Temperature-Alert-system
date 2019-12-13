import conf, time, math, statistics
from boltiot import Bolt
import json,requests
def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
history_data = []
def send_telegram_message(message):
    """Sends message via Telegram"""
    url = "https://api.telegram.org/" + conf.TELEGRAM_BOT_ID + "/sendMessage"
    data = {
        "chat_id": conf.TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.request(
            "POST",
            url,
            params=data
        )
        print("This is the Telegram URL")
        print(url)
        print("This is the Telegram response")
        print(response.text)
        telegram_data = json.loads(response.text)
        return telegram_data["ok"]
    except Exception as e:
        print("An error occurred in sending the alert message via Telegram")
        print(e)
        return False

while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue

    print ("This is the value "+data['value'])
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    if not bound:
        required_data_count=conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0] :
            print ("The temperature level increased suddenly. Sending an Email.")
            message = "Alert!, temperature has increased suddenly to" + str(sensor_value)
            telegram_status = send_telegram_message(message)
            print ("Current telegram status is" + str(telegram_status))
        elif sensor_value < bound[1]:
            print ("The temperature level decreased suddenly. Sending an Email.")
            message = "Alert!, temperature has decreased suddenly to" + str(sensor_value)
            telegram_status = send_telegram_message(message)
            print ("Current telegram status is" + str(telegram_status))
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10)