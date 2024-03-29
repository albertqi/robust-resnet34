import matplotlib.pyplot as plt
import sys, torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageNet
from torchvision.models import resnet34, ResNet34_Weights
from torchvision.transforms import v2
from tqdm import tqdm


DATA_DIR = "data/"
TRANSFORMS = [
    None,
    # Geometric transformations.
    v2.ElasticTransform(alpha=200.0, sigma=5.0),
    v2.RandomPerspective(distortion_scale=0.5, p=1.0),
    v2.RandomRotation(degrees=180.0),
    # Photometric transformations.
    v2.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.5, hue=0.5),
    v2.GaussianBlur(kernel_size=(9, 9), sigma=8.0),
    v2.RandomInvert(p=1.0),
    v2.RandomPosterize(bits=2, p=1.0),
]


def visualize(transform):
    """Visualize the transformation."""

    # Load the data.
    val_dataset = ImageNet(DATA_DIR, split="val", transform=transform)

    # Visualize the data.
    figure = plt.figure(figsize=(6, 6))
    cols, rows = 2, 2
    for i in range(1, cols * rows + 1):
        sample_idx = torch.randint(len(val_dataset), size=(1,)).item()
        img, label = val_dataset[sample_idx]
        figure.add_subplot(rows, cols, i)
        plt.title(f"Class {label}")
        plt.axis("off")
        plt.imshow(img)
    plt.show()


def val(transform):
    """Evaluate the model with the given transformation."""

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    # Define the preprocessing pipeline.
    weights = ResNet34_Weights.DEFAULT
    preprocessing = weights.transforms()

    # Load the data.
    transform = v2.Compose([preprocessing, transform]) if transform else preprocessing
    val_dataset = ImageNet(DATA_DIR, split="val", transform=transform)
    val_dataloader = DataLoader(val_dataset, batch_size=32, num_workers=8)

    # Define the model.
    model = resnet34(weights=weights).to(device)

    # Define the loss function.
    loss_fn = nn.CrossEntropyLoss()

    # Evaluate the model.
    losses, accuracies = [], []
    model.eval()
    for X, y in tqdm(val_dataloader):
        X, y = X.to(device), y.to(device)

        with torch.no_grad():
            l = model(X)
        J = loss_fn(l, y)

        losses.append(J.item())
        accuracies.append(y.eq(l.detach().argmax(dim=1)).float().mean())

    avg_loss = torch.tensor(losses).mean()
    avg_accuracy = torch.tensor(accuracies).mean()

    print(transform)
    print(f"Avg. Validation Loss: {avg_loss:.2f}")
    print(f"Avg. Validation Accuracy: {avg_accuracy:.2f}")
    print()


def main():
    assert len(sys.argv) == 2
    should_visualize = sys.argv[1] == "1"

    for transform in TRANSFORMS:
        if should_visualize:
            visualize(transform)
        else:
            val(transform)


if __name__ == "__main__":
    main()
