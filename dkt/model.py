import torch
import torch.nn as nn


class DKTModel(nn.Module):

    def __init__(
        self,
        input_size=2,
        hidden_size=64,
        num_layers=2
    ):

        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )

        self.output = nn.Sequential(

            nn.Linear(
                hidden_size,
                32
            ),

            nn.ReLU(),

            nn.Linear(
                32,
                1
            ),

            nn.Sigmoid()
        )

    def forward(self, x):

        lstm_out, _ = self.lstm(x)

        mastery = self.output(
            lstm_out
        ).squeeze(-1)

        return mastery