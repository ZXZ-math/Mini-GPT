"""
Training file for the models we implemented 
"""

from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
import os

import torch.optim as optim
import torch.nn.utils
from torch.utils.data import DataLoader
from einops import rearrange
import wandb

from model import BigramLanguageModel, MiniGPT
from dataset import TinyStoriesDataset
from config import BigramConfig, MiniGPTConfig


MODEL = "minigpt"  # bigram or minigpt

if MODEL == "bigram":
    config = BigramConfig
    model = BigramLanguageModel(config)
elif MODEL == "minigpt":
    config = MiniGPTConfig
    model = MiniGPT(config)
else:
    raise ValueError("Invalid model name")


# Initialize wandb if you want to use it
if config.to_log:
    wandb.init(project="dl2_proj3_minigpt")


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


train_dataset = TinyStoriesDataset(
    config.path_to_data,
    mode="train",
    context_length=config.context_length,
)
eval_dataset = TinyStoriesDataset(
    config.path_to_data, mode="test", context_length=config.context_length
)

train_dataloader = DataLoader(
    train_dataset, batch_size=config.batch_size, pin_memory=True
)
eval_dataloader = DataLoader(
    eval_dataset, batch_size=config.batch_size, pin_memory=True
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("number of trainable parameters: %.2fM" % (count_parameters(model) / 1e6,))


if not Path.exists(config.save_path):
    Path.mkdir(MiniGPTConfig.save_path, parents=True, exist_ok=True)


### ==================== START OF YOUR CODE ==================== ###
"""
You are required to implement the training loop for the model.

Please keep the following in mind:
- You will need to define an appropriate loss function for the model.
- You will need to define an optimizer for the model.
- You are required to log the loss (either on wandb or any other logger you prefer) every `config.log_interval` iterations.
- It is recommended that you save the model weights every `config.save_iterations` iterations you can also just save the model with the best training loss.

Please check the config file to see the different configurations you can set for the model.
NOTE :
The MiniGPT config has params that you do not need to use, these were added to scale the model but are
not a required part of the assignment.
Feel free to experiment with the parameters and I would be happy to talk to you about them if interested :)
"""

def save_checkpoint(save_path, model, optimizer, dmconfig):
    save_ckpt = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'dmconfig': dmconfig
    }
    torch.save(save_ckpt, save_path)


optimizer = optim.Adam(model.parameters(), lr=1e-4)

def train_and_test(train_dataloader,eval_dataloader, model, optimizer,device,test_length=1000):
    model = model.to(device)
    model.train()
    criterion = nn.CrossEntropyLoss()
    for i,(x,y) in enumerate(tqdm(train_dataloader,leave = True, desc = 'training')):
        x,y = x.to(device),y.to(device)
        predicted_y = model(x)
        #y = y.squeeze(1)
        predicted_y = torch.transpose(predicted_y,1,2)
        loss = criterion(predicted_y,y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if i%config.log_interval==0:
          wandb.log({"training loss": loss})
        if i%config.save_iterations == 0:
          nth_check_point = str(i//config.save_iterations) + 'save_iterations_checkpoint.pth'
          save_best_path = os.path.join(config.save_path, nth_check_point)
          save_checkpoint(save_best_path, model, optimizer, config)
        if i%1000 == 0:
          test_loss = test(eval_dataloader=eval_dataloader,model=model,device=device,test_length=test_length)
          wandb.log({"test loss": test_loss})
        if i == len(train_dataloader)-1:
          break
    return

def test(eval_dataloader,model,device,test_length):
    model.eval()
    criterion = nn.CrossEntropyLoss()
    test_loss = 0
    with torch.no_grad():
      for i,(x,y) in enumerate(eval_dataloader):
        x,y = x.to(device),y.to(device)
        predicted_y = model(x)
        predicted_y = torch.transpose(predicted_y,1,2)
        #y = y.squeeze(1)
        test_loss += criterion(predicted_y,y).item()
        predicted_y = None
        if i==test_length-1:
          break
      loss = test_loss/i
    return loss


train_and_test(train_dataloader=train_dataloader,eval_dataloader=eval_dataloader, model=model, optimizer=optimizer,device=device)