# The simplist example of using collie, enjoy 3D parallism!
# Command CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 torchrun --rdzv_backend=c10d --rdzv_endpoint=localhost:29402 --nnodes=1 --nproc_per_node=8 alpaca.py
import sys
sys.path.append("/mnt/petrelfs/gutianle/Megatron-LM/")
sys.path.append("/mnt/petrelfs/gutianle/collie/")
from transformers import LlamaTokenizer
from collie.trainer.trainer import Trainer
from collie.models.llama.model import LlamaModel
from collie.models.llama.arguments import LlamaArguments
from collie.metrics.decode import DecodeMetric
from transformers.generation.utils import GenerationConfig
from torch.utils.data import Dataset
import torch
import json

tokenizer = LlamaTokenizer.from_pretrained("decapoda-research/llama-7b-hf", 
                                           padding_side="left")
tokenizer.pad_token_id = 0
tokenizer.bos_token_id = 1
tokenizer.eos_token_id = 2

args = LlamaArguments.from_pretrained("decapoda-research/llama-7b-hf")
args.pp_size = 2
args.tp_size = 2
args.train_epochs = 10
args.train_micro_batch_size = 1
args.eval_batch_size = 1
args.eval_per_n_steps = 2
args.ds_config = {
    "fp16": {"enabled": True},
    "optimizer": {
        "type": "Adam",
        "params": {
            "lr": 2e-5
        }
    }
}


# Alpaca数据
class AlpacaDataset(Dataset):
    def __init__(self, data_path):
        self.alpaca = self.load_data(data_path)
        
    def load_data(self, data_path):
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def __len__(self):
        return len(self.alpaca)
    
    def __getitem__(self, idx):
        return self.alpaca[idx]
    
def train_collate_fn(batch):
    # input_ids_list = []
    # label_ids_list = []
    batch_inputs = []
    for sample in batch:
        batch_inputs.append(sample['prompt'] + sample['label'])
        # sample_label = tokenizer.bos_token + sample['prompt'] + sample['label'] + tokenizer.eos_token
        # sample_input = sample_label
        # input_ids = tokenizer.encode(sample_input, add_special_tokens=False)
        # label_ids = tokenizer.encode(sample_label, add_special_tokens=False)
        # prompt_len = len(tokenizer.encode(sample['prompt'], add_special_tokens=False))
        # input_ids = input_ids[1:prompt_len+1] + [tokenizer.pad_token_id] * (len(label_ids) - prompt_len -1)
        # label_ids = [-100] * (prompt_len + 1) + label_ids[prompt_len + 1:]
        # input_ids_list.append(torch.tensor(input_ids))
        # label_ids_list.append(torch.tensor(label_ids))
    input_ids = tokenizer(batch_inputs, return_tensors="pt", add_eos_token=True)["input_ids"]
    # input_ids = torch.nn.utils.rnn.pad_sequence(input_ids_list, batch_first=True)
    # label_ids = torch.nn.utils.rnn.pad_sequence(label_ids_list, batch_first=True)
    return input_ids, input_ids

def eval_collate_fn(batch):
    batch_inputs = []
    for sample in batch:
        batch_inputs.append(sample['prompt'])
    input_ids = tokenizer(batch_inputs, return_tensors="pt", add_eos_token=False)["input_ids"]
    return input_ids, input_ids  

dataset = AlpacaDataset('alpaca_data.json')
print(dataset[0])
# train_dataset = dataset[:-32]
# eval_dataset = dataset[-32:]

# model = LlamaModel(args)
# state_dict = LlamaModel.load_parallel_state_dict(
#     path="hdd:s3://opennlplab_hdd/models/llama/llama-7b-hf/",
#     protocol="petrel",
#     format="hf",
#     process_exclusion=False,
#     args=args)
# model.load_state_dict(state_dict)

# trainer = Trainer(
#     model = model,
#     train_dataset=train_dataset,
#     eval_dataset=eval_dataset,
#     train_dataset_collate_fn=train_collate_fn,
#     eval_dataset_collate_fn=eval_collate_fn,
#     eval_config=GenerationConfig(max_new_tokens=128, eos_token_id=2, pad_token_id=0, bos_token_id=1),
#     metrics=[DecodeMetric(tokenizer=tokenizer)],
#     args=args
# )

# torch.cuda.empty_cache()
# trainer.train()