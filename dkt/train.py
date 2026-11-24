#train.py
import torch
from torch.utils.data import DataLoader

from dataset import DKTDataset
from model import DKTModel

from pathlib import Path


dataset = DKTDataset(
    num_students=10000,
    sequence_length=30
)

loader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True
)


model = DKTModel()


criterion = torch.nn.MSELoss()


optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001
)


EPOCHS = 100


for epoch in range(EPOCHS):

    total_loss = 0.0

    for x, target in loader:

        prediction = model(x)

        loss = criterion(
            prediction,
            target
        )

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        total_loss += loss.item()


    if epoch % 10 == 0:

        average_loss = (
            total_loss / len(loader)
        )

        print(
            f"Epoch {epoch} "
            f"Loss: {average_loss:.4f}"
        )


MODEL_PATH = (
    Path(__file__).parent
    / "dkt_model.pt"
)


torch.save(
    model.state_dict(),
    MODEL_PATH
)


print("DKT model saved.")