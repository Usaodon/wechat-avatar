from transformers import AutoTokenizer, AutoModel
from peft import PeftModel
import torch
import numpy as np


device = 'cuda'

model_name_or_path = '/data/wll/ChatGLM/model_weight_chatglm2_6b'
adapter_name_or_path = '/data/wdm/wechat/output/chatglm2-6b/checkpoint-1382'

tokenizer = AutoTokenizer.from_pretrained(
    model_name_or_path,
    trust_remote_code=True
)
model = AutoModel.from_pretrained(
    model_name_or_path,
    trust_remote_code=True,
    low_cpu_mem_usage=True,
    torch_dtype=torch.float16,
    device_map=device
)
model = PeftModel.from_pretrained(model, adapter_name_or_path)
model = model.merge_and_unload()

model.eval()
model.to(device)

print('Done')

def inference_main(utterances):
    utterances_ids = tokenizer(utterances, add_special_tokens=False).input_ids
    utterances_ids[0] = [64790, 64792] + utterances_ids[0]

    # 模型的输入格式为：<s>input1</s>target1</s>input2</s>target2</s>...
    input_ids = []
    for i, utterances_id in enumerate(utterances_ids):
        input_ids += (utterances_id + [64792])

    model_input = ' '.join(utterances)
    inputs = tokenizer(model_input, return_tensors='pt')

    attention_mask = list(inputs['attention_mask'].numpy()[0])
    attention_mask += [1] * (len(utterances))
    attention_mask = np.array([attention_mask])

    position_ids = list(inputs['position_ids'].numpy()[0])
    position_ids += [position_ids[-1] + i for i in range(len(utterances))]
    position_ids = np.array([position_ids])

    inputs['input_ids'] = torch.LongTensor([input_ids])
    inputs['attention_mask'] = torch.LongTensor(attention_mask)
    inputs['position_ids'] = torch.LongTensor(position_ids)

    inputs = inputs.to(device)

    # print('Input ids processed: {}'.format(inputs))
    pred = model.generate(**inputs, max_new_tokens=64, repetition_penalty=1.1)
    pred_ids = list(pred.cpu()[0].numpy())[2:]
    str_pred_ids = [str(p) for p in pred_ids]
    chats = ' '.join(str_pred_ids).split('64792')
    preds = [int(c) for c in chats[len(utterances)].strip().split(' ')]
    # print('Pred ids: {}'.format(preds))

    res = tokenizer.decode(preds, skip_special_tokens=True)
    return res


if __name__ == '__main__':
    sent = ['请你扮演一位微信用户“乌冬面”，并根据聊天记录以及不同用户的输入作出响应。', '老婆:阿东', '乌冬面:[手机图片]<s>我刚到<s>你在哪呢']
    res = inference_main(sent)
