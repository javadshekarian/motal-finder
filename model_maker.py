import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

INPUT_FILE = "DATA.bin"
OUTPUT_FILE = "METAL_MODEL.pt"

PHASES = 201

EPOCHS = 80
BATCH_SIZE = 128
LEARNING_RATE = 0.001

VALIDATION_RATIO = 0.20
THRESHOLD_PERCENTILE = 99.5

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ConvAutoencoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv1d(1, 16, 5, stride=2, padding=2),
            nn.ReLU(),

            nn.Conv1d(16, 32, 5, stride=2, padding=2),
            nn.ReLU(),

            nn.Conv1d(32, 16, 5, stride=2, padding=2),
            nn.ReLU()
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(
                16,
                32,
                5,
                stride=2,
                padding=2,
                output_padding=0
            ),
            nn.ReLU(),

            nn.ConvTranspose1d(
                32,
                16,
                5,
                stride=2,
                padding=2,
                output_padding=0
            ),
            nn.ReLU(),

            nn.ConvTranspose1d(
                16,
                1,
                5,
                stride=2,
                padding=2,
                output_padding=0
            )
        )

    def forward(self, x):

        encoded = self.encoder(x)
        decoded = self.decoder(encoded)

        decoded = decoded[:, :, :PHASES]

        if decoded.shape[2] < PHASES:
            decoded = nn.functional.pad(
                decoded,
                (0, PHASES - decoded.shape[2])
            )

        return decoded


data = np.fromfile(
    INPUT_FILE,
    dtype="<u2"
).astype(np.float32)

wave_count = len(data) // PHASES

if wave_count < 100:
    raise RuntimeError(
        f"Not enough complete waveforms: {wave_count}"
    )

data = data[:wave_count * PHASES]

waves = data.reshape(
    wave_count,
    PHASES
)

np.random.seed(42)

indices = np.random.permutation(wave_count)

waves = waves[indices]

validation_count = int(
    wave_count * VALIDATION_RATIO
)

train_waves = waves[:-validation_count]
validation_waves = waves[-validation_count:]

mean = np.mean(
    train_waves,
    axis=0
)

scale = np.std(
    train_waves
)

if scale < 0.1:
    scale = 0.1

train_normalized = (
    train_waves - mean
) / scale

validation_normalized = (
    validation_waves - mean
) / scale

train_tensor = torch.from_numpy(
    train_normalized
).float().unsqueeze(1)

validation_tensor = torch.from_numpy(
    validation_normalized
).float().unsqueeze(1)

train_loader = DataLoader(
    TensorDataset(train_tensor),
    batch_size=BATCH_SIZE,
    shuffle=True
)

model = ConvAutoencoder().to(DEVICE)

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)

loss_function = nn.MSELoss()

print("TRAINING MODEL")
print("--------------")
print(f"Device:          {DEVICE}")
print(f"Waveforms:       {wave_count}")
print(f"Training:        {len(train_waves)}")
print(f"Validation:      {len(validation_waves)}")
print(f"Phases:          {PHASES}")

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0.0

    for batch, in train_loader:

        batch = batch.to(DEVICE)

        optimizer.zero_grad()

        reconstructed = model(batch)

        loss = loss_function(
            reconstructed,
            batch
        )

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    average_loss = (
        total_loss /
        len(train_loader)
    )

    if (
        epoch == 0
        or (epoch + 1) % 10 == 0
    ):
        print(
            f"Epoch {epoch + 1:3d}/{EPOCHS} | "
            f"Loss: {average_loss:.6f}"
        )


model.eval()

with torch.no_grad():

    validation_input = validation_tensor.to(DEVICE)

    validation_output = model(
        validation_input
    )

    errors = torch.mean(
        (
            validation_output -
            validation_input
        ) ** 2,
        dim=(1, 2)
    )

    errors = errors.cpu().numpy()

threshold = float(
    np.percentile(
        errors,
        THRESHOLD_PERCENTILE
    )
)

train_error = float(
    np.mean(errors)
)

max_error = float(
    np.max(errors)
)

torch.save(
    {
        "model_state": model.state_dict(),
        "mean": mean.astype(np.float32),
        "scale": np.float32(scale),
        "threshold": np.float32(threshold),
        "phases": PHASES
    },
    OUTPUT_FILE
)

print()
print("MODEL CREATED")
print("-------------")
print(f"Output:          {OUTPUT_FILE}")
print(f"Waveforms:       {wave_count}")
print(f"Validation:      {len(validation_waves)}")
print(f"Mean error:      {train_error:.6f}")
print(f"Max error:       {max_error:.6f}")
print(f"Threshold:       {threshold:.6f}")
print(f"Percentile:      {THRESHOLD_PERCENTILE}")
