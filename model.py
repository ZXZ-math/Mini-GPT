## Building and training a bigram language model
from functools import partial
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import einsum, reduce, rearrange


class BigramLanguageModel(nn.Module):
    """
    Class definition for a simple bigram language model.
    """

    def __init__(self, config):
        """
        Initialize the bigram language model.

        The model should have the following layers:
        1. An embedding layer that maps tokens to embeddings. (self.embeddings)
        2. A linear layer that maps embeddings to logits. (self.linear) **set bias to True**
        3. A dropout layer. (self.dropout)

        NOTE : PLEASE KEEP OF EACH LAYER AS PROVIDED BELOW TO FACILITATE TESTING.
        """

        super().__init__()
        # ========= TODO : START ========= #
        self.embeddings = nn.Embedding(config.vocab_size, config.embed_dim)
        self.linear = nn.Linear(config.embed_dim,config.vocab_size,bias=True)
        self.dropout = nn.Dropout(config.dropout)

        # ========= TODO : END ========= #

        self.apply(self._init_weights)

    def forward(self, x):
        """
        Forward pass of the bigram language model.

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, 1) containing the input tokens.
        
        Output:
        torch.Tensor
            A tensor of shape (batch_size, vocab_size) containing the logits.
        """

        # ========= TODO : START ========= #

        # Embedding layer
        x = self.embeddings(x)  # shape: (batch_size,1,embed_dim)

        # Linear layer
        x = self.linear(x)  # shape: (batch_size, 1, vocab_size)
        
        # Dropout layer
        x = self.dropout(x)  # shape: (batch_size, 1, vocab_size)
        
        # Remove the second dimension (which is 1)
        x = x.squeeze(1)  # shape: (batch_size, vocab_size)
        

        return x
       

        # ========= TODO : END ========= #

    def _init_weights(self, module):
        """
        Weight initialization for better convergence.

        NOTE : You do not need to modify this function.
        """

        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def generate(self, context, max_new_tokens=100):
        """
        Use the model to generate new tokens given a context.
        We will perform multinomial sampling which is very similar to greedy sampling
        but instead of taking the token with the highest probability, we sample the next token from a multinomial distribution.


        Args:
        context : List[int]
            A list of integers (tokens) representing the context.
        max_new_tokens : int
            The maximum number of new tokens to generate.

        Output:
        List[int]
            A list of integers (tokens) representing the generated tokens.
        """

        ### ========= TODO : START ========= ###

        self.eval()
        context = context.unsqueeze(0)
        # Generate new tokens
        with torch.no_grad():
            for _ in range(max_new_tokens):
                 # Get the logits from the model
                logits = self.forward(context)  # (batch_size, seq_len, vocab_size)
                
                # Focus only on the last token's logits
                logits = logits[:, -1, :]  # (batch_size, vocab_size)
                
                # Apply softmax to get probabilities
                probs = F.softmax(logits, dim=-1)  # (batch_size, vocab_size)
                
                # Sample from the distribution
                next_token = torch.multinomial(probs, num_samples=1)  # (batch_size, 1)
                
                # Append the new token to the context
                context = torch.cat([context, next_token], dim=1)  # (batch_size, seq_len + 1)
        
        
        # Return the generated tokens as a list
        
        return context

        ### ========= TODO : END ========= ###


class SingleHeadAttention(nn.Module):
    """
    Class definition for Single Head Causal Self Attention Layer.

    As in Attention is All You Need (https://arxiv.org/pdf/1706.03762)

    """

    def __init__(
        self,
        input_dim,
        output_key_query_dim=None,
        output_value_dim=None,
        dropout=0.1,
        max_len=512,
    ):
        """
        Initialize the Single Head Attention Layer.

        The model should have the following layers:
        1. A linear layer for key. (self.key) **set bias to False**
        2. A linear layer for query. (self.query) **set bias to False**
        3. A linear layer for value. (self.value) # **set bias to False**
        4. A dropout layer. (self.dropout)
        5. A causal mask. (self.causal_mask) This should be registered as a buffer.
        NOTE : Please make sure that the causal mask is upper triangular and not lower triangular (this helps in setting up the test cases, )

         NOTE : PLEASE KEEP OF EACH LAYER AS PROVIDED BELOW TO FACILITATE TESTING.
        """
        super().__init__()

        self.input_dim = input_dim
        if output_key_query_dim:
            self.output_key_query_dim = output_key_query_dim
        else:
            self.output_key_query_dim = input_dim

        if output_value_dim:
            self.output_value_dim = output_value_dim
        else:
            self.output_value_dim = input_dim

        causal_mask = None  # You have to implement this, currently just a placeholder

        # ========= TODO : START ========= #

        # self.key = ...
        # self.query = ...
        # self.value = ...
        # self.dropout = ...

        # causal_mask = ...
        
        self.key = nn.Linear(self.input_dim,self.output_key_query_dim,bias=False)
        self.query = nn.Linear(self.input_dim,self.output_key_query_dim,bias=False)
        self.value = nn.Linear(self.input_dim,self.output_value_dim,bias=False)
        self.dropout = nn.Dropout(dropout)
        causal_mask = torch.zeros((max_len, max_len)) + torch.triu(torch.full((max_len, max_len), float('-inf')), diagonal=1)
        # ========= TODO : END ========= #

        self.register_buffer(
            "causal_mask", causal_mask
        )  # Registering as buffer to avoid backpropagation

    def forward(self, x):
        """
        Forward pass of the Single Head Attention Layer.

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, num_tokens, output_value_dim) containing the output tokens.
        """

        # ========= TODO : START ========= #
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        num_tokens = x.size(1)
        prod = torch.matmul(Q,torch.transpose(K,1,2))
        device = x.get_device()
        causal_mask = torch.zeros((num_tokens, num_tokens)) + torch.triu(torch.full((num_tokens, num_tokens), float('-inf')), diagonal=1)
        prod += causal_mask.to(device)
        #prod += self.causal_mask[:num_tokens,:num_tokens]
        prod = prod/math.sqrt(self.output_key_query_dim)
        prod = F.softmax(prod,dim=2)
        result = torch.matmul(prod,V)
        return result

        # ========= TODO : END ========= #


class MultiHeadAttention(nn.Module):
    """
    Class definition for Multi Head Attention Layer.

    As in Attention is All You Need (https://arxiv.org/pdf/1706.03762)
    """

    def __init__(self, input_dim, num_heads, dropout=0.1) -> None:
        """
        Initialize the Multi Head Attention Layer.

        The model should have the following layers:
        1. Multiple SingleHeadAttention layers. (self.head_{i}) Use setattr to dynamically set the layers.
        2. A linear layer for output. (self.out) **set bias to True**
        3. A dropout layer. (self.dropout) Apply dropout to the output of the out layer.

        NOTE : PLEASE KEEP OF EACH LAYER AS PROVIDED BELOW TO FACILITATE TESTING.
        """
        super().__init__()

        self.input_dim = input_dim
        self.num_heads = num_heads

        # ========= TODO : START ========= #

        # self.head_{i} = ... # Use setattr to implement this dynamically, this is used as a placeholder
        # self.out = ...
        # self.dropout = ...
        
        for i in range(num_heads):
            setattr(self,f'head_{i}',SingleHeadAttention(input_dim = input_dim,
            output_key_query_dim=input_dim//num_heads,
            output_value_dim = input_dim//num_heads
            ))
        self.out = nn.Linear(input_dim, input_dim,bias=True)
        self.dropout = nn.Dropout(dropout)

        # ========= TODO : END ========= #

    def forward(self, x):
        """
        Forward pass of the Multi Head Attention Layer.

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the output tokens.
        """

        # ========= TODO : START ========= #
        head_output = []
        for i in range(self.num_heads):
            head = getattr(self,f'head_{i}')
            y = head(x)
            
            head_output.append(y)
        
        y = torch.cat(head_output,dim=-1)
        y = self.out(y)
        y = self.dropout(y)

        # ========= TODO : END ========= #
        return y 

class FeedForwardLayer(nn.Module):
    """
    Class definition for Feed Forward Layer.
    """

    def __init__(self, input_dim, feedforward_dim=None, dropout=0.1):
        """
        Initialize the Feed Forward Layer.

        The model should have the following layers:
        1. A linear layer for the feedforward network. (self.fc1) **set bias to True**
        2. A GELU activation function. (self.activation)
        3. A linear layer for the feedforward network. (self.fc2) ** set bias to True**
        4. A dropout layer. (self.dropout)

        NOTE : PLEASE KEEP OF EACH LAYER AS PROVIDED BELOW TO FACILITATE TESTING.
        """
        super().__init__()

        if feedforward_dim is None:
            feedforward_dim = input_dim * 4

        # ========= TODO : START ========= #

        # self.fc1 = ...
        # self.activation = ...
        # self.fc2 = ...
        # self.fc2 = ...
        # self.dropout = ...
        self.fc1 = nn.Linear(input_dim,feedforward_dim,bias = True)
        self.activation = nn.GELU()
        self.fc2= nn.Linear(feedforward_dim,input_dim,bias = True)
        self.dropout = nn.Dropout(dropout)
        

        # ========= TODO : END ========= #

    def forward(self, x):
        """
        Forward pass of the Feed Forward Layer.

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the output tokens.
        """

        ### ========= TODO : START ========= ###

        model = nn.Sequential(
            self.fc1,
            self.activation,
            self.fc2,
            self.dropout
            )
        x = model(x)

        ### ========= TODO : END ========= ###
        return x 

class LayerNorm(nn.Module):
    """
    LayerNorm module as in the paper https://arxiv.org/abs/1607.06450

    Note : Variance computation is done with biased variance.
    """

    def __init__(self, normalized_shape, eps=1e-05, elementwise_affine=True) -> None:
        super().__init__()

        self.normalized_shape = (normalized_shape,)
        self.eps = eps
        self.elementwise_affine = elementwise_affine

        if elementwise_affine:
            self.gamma = nn.Parameter(torch.ones(tuple(self.normalized_shape)))
            self.beta = nn.Parameter(torch.zeros(tuple(self.normalized_shape)))

    def forward(self, input):
        """
        Forward pass of the LayerNorm Layer.

        Args:
        input : torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the output tokens.
        """

        # ========= TODO : START ========= #
        mean = input.mean(dim=-1,keepdim = True)
        var = input.var(dim=-1,keepdim=True,unbiased=False)
        
        normalized_input = (input - mean)/torch.sqrt(var + self.eps) 
        
        if self.elementwise_affine:
            normalized_input = self.beta + normalized_input * self.gamma
        
        return normalized_input         

        # ========= TODO : END ========= #


class TransformerLayer(nn.Module):
    """
    Class definition for a single transformer layer.
    """

    def __init__(self, input_dim, num_heads, feedforward_dim=None):
        super().__init__()
        """
        Initialize the Transformer Layer.
        We will use prenorm layer where we normalize the input before applying the attention and feedforward layers.

        The model should have the following layers:
        1. A LayerNorm layer. (self.norm1)
        2. A MultiHeadAttention layer. (self.attention)
        3. A LayerNorm layer. (self.norm2)
        4. A FeedForwardLayer layer. (self.feedforward)

        NOTE : PLEASE KEEP OF EACH LAYER AS PROVIDED BELOW TO FACILITATE TESTING.
        """

        # ========= TODO : START ========= #

        # self.norm1 = ...
        # self.attention = ...
        # self.norm2 = ...
        # self.feedforward = ...
        self.norm1 = LayerNorm(normalized_shape=input_dim)
        self.attention = MultiHeadAttention(input_dim = input_dim , num_heads = num_heads)
        self.norm2 = LayerNorm(normalized_shape=input_dim)
        self.feedforward = FeedForwardLayer(input_dim = input_dim,feedforward_dim=None)

        # ========= TODO : END ========= #

    def forward(self, x):
        """
        Forward pass of the Transformer Layer.

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, num_tokens, token_dim) containing the output tokens.
        """

        # ========= TODO : START ========= #

        x1 = self.norm1(x)
        x1 = self.attention(x1)
        x = x + x1 
        x1 = self.norm2(x)
        x1 = self.feedforward(x1)
        x = x + x1

        # ========= TODO : END ========= #
        return x 

class MiniGPT(nn.Module):
    """
    Putting it all together: GPT model
    """

    def __init__(self, config) -> None:
        super().__init__()
        """
        Putting it all together: our own GPT model!

        Initialize the MiniGPT model.

        The model should have the following layers:
        1. An embedding layer that maps tokens to embeddings. (self.vocab_embedding)
        2. A positional embedding layer. (self.positional_embedding) We will use learnt positional embeddings. 
        3. A dropout layer for embeddings. (self.embed_dropout)
        4. Multiple TransformerLayer layers. (self.transformer_layers)
        5. A LayerNorm layer before the final layer. (self.prehead_norm)
        6. Final language Modelling head layer. (self.head) We will use weight tying (https://paperswithcode.com/method/weight-tying) and set the weights of the head layer to be the same as the vocab_embedding layer.

        NOTE: You do not need to modify anything here.
        """
        self.context_length = config.context_length
        self.vocab_embedding = nn.Embedding(config.vocab_size, config.embed_dim)
        self.positional_embedding = nn.Embedding(
            config.context_length, config.embed_dim
        )
        self.embed_dropout = nn.Dropout(config.embed_dropout)

        self.transformer_layers = nn.ModuleList(
            [
                TransformerLayer(
                    config.embed_dim, config.num_heads, config.feedforward_size
                )
                for _ in range(config.num_layers)
            ]
        )

        # prehead layer norm
        self.prehead_norm = LayerNorm(config.embed_dim)

        self.head = nn.Linear(
            config.embed_dim, config.vocab_size
        )  # Language modelling head

        if config.weight_tie:
            self.head.weight = self.vocab_embedding.weight

        # precreate positional indices for the positional embedding
        pos = torch.arange(0, config.context_length, dtype=torch.long)
        self.register_buffer("pos", pos, persistent=False)

        self.apply(self._init_weights)

    def forward(self, x):
        """
        Forward pass of the MiniGPT model.

        Remember to add the positional embeddings to your input token!!

        Args:
        x : torch.Tensor
            A tensor of shape (batch_size, seq_len) containing the input tokens.

        Output:
        torch.Tensor
            A tensor of shape (batch_size, seq_len, vocab_size) containing the logits.
        """

        ### ========= TODO : START ========= ###
        seq_len = x.size(1)
        x = self.vocab_embedding(x) # (batch_size, seq_len, embed_dim)
        pos_embed = self.positional_embedding(self.pos[:seq_len]) # (seq_len, embed_dim)
        pos_embed = self.embed_dropout(pos_embed) # (seq_len, embed_dim)
        x += pos_embed # (batch_size, seq_len, embed_dim) 
        for layers in self.transformer_layers:
            x = layers(x) # (batch_size, seq_len, embed_dim) 
        x = self.prehead_norm(x) # (batch_size, seq_len, embed_dim) 
        x = self.head(x)  # (batch_size, seq_len, vocab_size) 

        ### ========= TODO : END ========= ###
        return x 
        
    def _init_weights(self, module):
        """
        Weight initialization for better convergence.

        NOTE : You do not need to modify this function.
        """

        if isinstance(module, nn.Linear):
            if module._get_name() == "fc2":
                # GPT-2 style FFN init
                torch.nn.init.normal_(
                    module.weight, mean=0.0, std=0.02 / math.sqrt(2 * self.num_layers)
                )
            else:
                torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def generate(self, context, max_new_tokens=100):
        """
        Use the model to generate new tokens given a context.

        Please copy the generate function from the BigramLanguageModel class you had implemented earlier.
        """
        context = context.unsqueeze(0)
        # Generate new tokens
        with torch.no_grad():
            for _ in range(max_new_tokens):
                # Get the logits from the model
                logits = self.forward(context[:,-self.context_length:])  # (batch_size, seq_len, vocab_size)
                
                # Focus only on the last token's logits
                logits = logits[:, -1, :]  # (batch_size, vocab_size)
                
                # Apply softmax to get probabilities
                probs = F.softmax(logits, dim=-1)  # (batch_size, vocab_size)
                
                # Sample from the distribution
                next_token = torch.multinomial(probs, num_samples=1)  # (batch_size, 1)
                
                # Append the new token to the context
                context = torch.cat([context, next_token], dim=1)  # (batch_size, seq_len + 1)
        
        
        # Return the generated tokens as a list
        
        return context

        ### ========= TODO : END ========= ###
