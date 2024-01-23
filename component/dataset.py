import json
from loguru import logger
from torch.utils.data import Dataset


class SFTDataset(Dataset):
    def __init__(self, file, tokenizer, max_seq_length):
        self.tokenizer = tokenizer
        self.bos_token = tokenizer.special_tokens_map['bos_token']
        self.bos_token_id = tokenizer.vocab[self.bos_token]

        self.eos_token = tokenizer.special_tokens_map['eos_token']
        self.eos_token_id = tokenizer.vocab[self.eos_token]

        # self.gmask_token_id = tokenizer.special_tokens_map['[gMASK]']
        # self.gmask_token = '[gMASK]'

        self.max_seq_length = max_seq_length
        logger.info('Loading data: {}'.format(file))
        with open(file, 'r', encoding='utf8') as f:
            data_list = f.readlines()
        logger.info("there are {} data in dataset".format(len(data_list)))
        self.data_list = data_list

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        # 每条数据格式为: <s>input1</s>target1</s>input2</s>target2</s>...
        data = self.data_list[index]
        data = json.loads(data)
        conversation = data['conversation']

        # 收集多轮对话
        utterances = []
        for x in conversation:
            utterances.append(x['human'])
            utterances.append(x['assistant'])
        utterances_ids = self.tokenizer(utterances, add_special_tokens=False).input_ids
        # utterances_ids[0] = [self.gmask_token_id, self.bos_token_id] + utterances_ids[0]
        utterances_ids[0] = [self.bos_token_id] + utterances_ids[0]

        # 模型的输入格式为：<s>input1</s>target1</s>input2</s>target2</s>...
        input_ids = []
        target_mask = []  # 用于对input进行mask，只计算target部分的loss
        for i, utterances_id in enumerate(utterances_ids):
            input_ids += (utterances_id + [self.eos_token_id])
            if i % 2 == 0:
                target_mask += [0] * (len(utterances_id) + 1)
            else:
                target_mask += [1] * (len(utterances_id) + 1)
        assert len(input_ids) == len(target_mask)
        # 对长度进行截断
        input_ids = input_ids[:self.max_seq_length]
        target_mask = target_mask[:self.max_seq_length]
        attention_mask = [1] * len(input_ids)
        assert len(input_ids) == len(target_mask) == len(attention_mask)
        inputs = {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'target_mask': target_mask
        }
        return inputs
