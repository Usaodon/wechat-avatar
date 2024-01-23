PYPATH=/data/miniconda3/envs/wdm/bin
CUDA_VISIBLE_DEVICES=7 $PYPATH/python train_lora.py --train_args_file train_args/lora/chatglm2-sft-qlora.json
