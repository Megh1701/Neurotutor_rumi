import torch
from torch.utils.data import Dataset


class DKTDataset(Dataset):

    def __init__(
        self,
        num_students=1000,
        sequence_length=20
    ):

        self.samples = []

        for _ in range(num_students):

            mastery = (
                torch.rand(1).item() * 0.4 + 0.2
            )

            sequence = []
            targets = []

            for _ in range(sequence_length):

                difficulty = torch.rand(1).item()

                probability = (
                    mastery
                    - 0.20 * difficulty
                )

                probability = max(
                    0.05,
                    min(0.95, probability)
                )

                correct = (
                    torch.rand(1).item()
                    < probability
                )

                # Record the interaction
                sequence.append([
                    float(correct),
                    difficulty
                ])

                # Update latent student mastery
                if correct:
                    mastery += 0.08
                else:
                    mastery -= 0.05

                mastery = max(
                    0.05,
                    min(0.95, mastery)
                )

                # TARGET = mastery AFTER this interaction
                targets.append(mastery)

            self.samples.append(
                (
                    torch.tensor(
                        sequence,
                        dtype=torch.float32
                    ),
                    torch.tensor(
                        targets,
                        dtype=torch.float32
                    )
                )
            )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        return self.samples[idx]