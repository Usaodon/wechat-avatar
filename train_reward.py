import torch
import json
import argparse
import evaluate
import torch.nn as nn
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModel,
    Trainer,
    HfArgumentParser,
    TrainingArguments,
    PreTrainedTokenizerBase
)
from torch.utils.data import Dataset
from dataclasses import dataclass
from random import random
from typing import Optional
from models.models import Chatglm2RewardModel
from peft.utils import TRANSFORMERS_MODELS_TO_LORA_TARGET_MODULES_MAPPING
from peft import LoraConfig, get_peft_model

# Define the metric that we'll use for validation.
accuracy = evaluate.load("accuracy")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name_or_path', type=str, default='/data2/model/chatglm2-6b')
    parser.add_argument('--dataset_path', type=str, default='data/reward_data/reward_raw.json')
    parser.add_argument('--train_args_json', type=str, default='train_args/lora/chatglm2-reward-lora.json')
    parser.add_argument('--max_len', type=int, default=512, help='max input length')
    parser.add_argument('--hidden_size', type=int, default=65024, help='hidden size')
    parser.add_argument('--lora_rank', type=int, default=4, help='lora_rank')
    parser.add_argument('--lora_alpha', type=int, default=32, help='lora_alpha')
    parser.add_argument('--lora_dropout', type=float, default=0.05, help='lora dropout')
    parser.add_argument('--batch_size', type=int, default=4, help='batch size')
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()
    return args


class RewardDataset(Dataset):
    def __init__(self, data, tokenizer):
        self.data = data
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.encode(self.data[index])

    def encode(self, item):
        source_id = self.tokenizer.encode(item['source'])
        reject_id = self.tokenizer.encode(item['reject'])
        accept_id = self.tokenizer.encode(item['accept'])

        reject_id = source_id + reject_id
        accept_id = source_id + accept_id
        return [reject_id, accept_id]


@dataclass
class RewardColloator:
    def __init__(self, tokenizer, max_length, device):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.device = device

    def __call__(self, sample):
        batch_reject_id, batch_accept_id = [], []
        for item in sample:
            batch_reject_id.append(item[0])
            batch_accept_id.append(item[1])

        batch_reject_id = torch.tensor(pad_sequence(batch_reject_id, self.max_length), dtype=torch.long)
        batch_accept_id = torch.tensor(pad_sequence(batch_accept_id, self.max_length), dtype=torch.long)

        output = {
            'reject_ids': batch_reject_id,
            'accept_ids': batch_accept_id,
        }
        return output


class RewardTrainer(Trainer):

    def compute_loss(self, model, inputs, return_outputs=False):
        rewards_j = model(reject_ids=inputs["reject_ids"])['reject_reward']

        rewards_k = model(accept_ids=inputs["accept_ids"])['accept_reward']

        loss = -nn.functional.logsigmoid(rewards_j - rewards_k).mean()

        if return_outputs:
            return loss, {"rewards_j": rewards_j, "rewards_k": rewards_k}
        return loss


def pad_sequence(seq, max_length):
    max_len = max([len(r) for r in seq])
    max_len = min(max_len, max_length)
    for s in seq:
        rest = max_len - len(s)
        s += [0] * rest
    return [s[:max_length] for s in seq]


def get_resp_list(item):
    scores = item['scores']
    scores_nonhop = set(scores)
    if len(scores) != 3 or len(scores_nonhop) != 3:
        return []
    resp_and_scores = [
        [item['resp1'], item['scores'][0]],
        [item['resp2'], item['scores'][1]],
        [item['resp3'], item['scores'][2]],
    ]
    resp_and_scores.sort(key=lambda x:x[1])
    # output:[rejected resp, accecpt resp]
    output = []
    for i in range(len(resp_and_scores) - 1):
        for j in range(i + 1, len(resp_and_scores)):
            output.append([resp_and_scores[i][0], resp_and_scores[j][0]])
    return output


def load_data(path):
    data = json.load(open(path, 'r', encoding='utf-8'))
    train_data, test_data = [], []
    for item in data:
        resp_list = get_resp_list(item)
        if len(resp_list):
            for pair in resp_list:
                temp = {
                    'source': item['source'],
                    'reject': pair[0],
                    'accept': pair[1]
                }
                n = random()
                if n < 0.8:
                    train_data.append(temp)
                else:
                    test_data.append(temp)
    return train_data, test_data


def compute_metrics(eval_pred, accuracy):
    predictions, _ = eval_pred
    # Here, predictions is rewards_j and rewards_k.
    # We want to see how much of the time rewards_j > rewards_k.
    predictions = np.argmax(predictions, axis=0)
    labels = np.zeros(predictions.shape)
    return accuracy.compute(predictions=predictions, references=labels)


def main(args):
    hf_parser = HfArgumentParser(TrainingArguments)
    training_args, = hf_parser.parse_json_file(json_file=args.train_args_json)

    train_data, test_data = load_data(args.dataset_path)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, trust_remote_code=True)

    trainset = RewardDataset(train_data, tokenizer)
    testset = RewardDataset(test_data, tokenizer)

    reward_model = Chatglm2RewardModel.from_pretrained(args.model_name_or_path, args, tokenizer)
    target_modules = TRANSFORMERS_MODELS_TO_LORA_TARGET_MODULES_MAPPING['chatglm']
    lora_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        target_modules=target_modules,
        lora_dropout=args.lora_dropout,
        bias='none',
        inference_mode=False,
    )
    reward_lora_model = get_peft_model(reward_model, lora_config)
    reward_lora_model.train()
    reward_lora_model.to(args.device)

    trainer = RewardTrainer(
        model=reward_lora_model,
        args=training_args,
        train_dataset=trainset,
        eval_dataset=testset,
        compute_metrics=compute_metrics,
        data_collator=RewardColloator(
            tokenizer=tokenizer, max_length=args.max_len, device=args.device),
    )

    trainer.train()


if __name__ == '__main__':
    args = parse_args()

    main(args)

