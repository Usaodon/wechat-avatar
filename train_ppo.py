import time
import math
import random
import warnings
import numpy as np
from models.models import *
from config import parse_args
from ppo.ppo_trainer import PPOTrainer
from ppo.ppo_datahelper import get_tokenizer
from utils import *
from peft import LoraConfig, LoraModel, TaskType, get_peft_model, PeftModel
from transformers import AutoModel, AutoTokenizer
from peft.utils import TRANSFORMERS_MODELS_TO_LORA_TARGET_MODULES_MAPPING
    
warnings.filterwarnings('ignore')


def main(opt):
    # setup accelerator
    accelerator = setup_accelerator()

    # setup deepspeed
    deepspeed_states = AcceleratorState().deepspeed_plugin
    deepspeed_states.deepspeed_config['train_micro_batch_size_per_gpu'] = opt.batch_size
    deepspeed_states.deepspeed_config['checkpoint'] = {'use_node_local_storage': True}

    # logging config
    logging.basicConfig(
            format='%(asctime)s - ' + f'Rank: {accelerator.process_index} - ' + '%(filename)s-->line:%(lineno)d' + ' - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging.INFO
            )
    logger = logging.getLogger(__name__)

    # fix seed
    random.seed(opt.seed)
    np.random.seed(opt.seed)
    torch.manual_seed(opt.seed)
    torch.cuda.manual_seed(opt.seed)

    # lora config

    # tokenizer
    tokenizer = get_tokenizer(opt)

    # load policy model
    logging.info(f"Loading policy model from: {opt.policy_model_path}...")
    policy_model = Llama.from_pretrained(opt.policy_model_path, opt, tokenizer)
    policy_lora_model = PeftModel.from_pretrained(policy_model, opt.policy_adaptor_path)
    policy_lora_model = policy_lora_model.merge_and_unload()
    policy_lora_model._set_gradient_checkpointing(policy_lora_model.base_model, opt.gradient_checkpoint)

    # load critic model
    logging.info(f"Loading critic model from: {opt.critic_model_path}...")
    critic_model = LlamaRewardModel.from_pretrained(opt.critic_model_path, opt, tokenizer)
    target_modules = TRANSFORMERS_MODELS_TO_LORA_TARGET_MODULES_MAPPING['llama']
    lora_config = LoraConfig(
        r=opt.lora_rank,
        lora_alpha=opt.lora_alpha,
        target_modules=target_modules,
        lora_dropout=opt.lora_dropout,
        bias='none',
        inference_mode=False,
    )
    critic_lora_model = get_peft_model(critic_model, lora_config)
    critic_lora_model._set_gradient_checkpointing(critic_lora_model.base_model, opt.gradient_checkpoint)

    # load reference model
    logging.info(f"Loading reference model from: {opt.policy_model_path}...")
    ref_model = Llama.from_pretrained(opt.policy_model_path, opt, tokenizer)
    ref_lora_model = PeftModel.from_pretrained(ref_model, opt.policy_adaptor_path)
    ref_lora_model = ref_lora_model.merge_and_unload()

    # load reward model
    logging.info(f"Loading reward model from: {opt.critic_model_path}...")
    reward_model = LlamaRewardModel.from_pretrained(opt.critic_model_path, opt, tokenizer)

    synchronize_if_distributed()
    trainer = PPOTrainer(opt, policy_lora_model, ref_lora_model, critic_lora_model, reward_model, accelerator)

    logging.info('==================Start Training...==================')
    trainer.train()

    logging.info('==================Congrats! Training completed, exit process...==================') 


if __name__ == '__main__':
    opt = parse_args()
    print_rank_0(opt)
    main(opt)
