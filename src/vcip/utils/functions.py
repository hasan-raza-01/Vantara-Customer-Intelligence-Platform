import random
import numpy as np
import torch

def set_seed(seed:int):
    """
    set seeding to a fixed number

    PARAMS: 
        - seed (int) : integer to fix seeding
    """
    random.seed(seed)  # Set seed for Python's random
    np.random.seed(seed)  # Set seed for NumPy
    torch.manual_seed(seed)  # Set seed for PyTorch (CPU)
    torch.cuda.manual_seed(seed)  # Set seed for PyTorch (GPU)


