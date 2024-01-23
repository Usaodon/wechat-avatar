from flask import Flask, request
import json
import time
from .inference import inference_main

app = Flask(__name__)

@app.route('/wechat/usaodon/chatglm_6b', methods=['POST'])
def inference_view():
    data = request.get_data().decode('utf-8')
    data = json.loads(data)
    print('Receive data:', str(data))
    model_input = data.get('input')

    stt = time.time()
    response = inference_main(model_input)
    end_time = time.time()
    output = json.dumps({'output': response, 'time': stt - end_time})
    print(output)
    return output
