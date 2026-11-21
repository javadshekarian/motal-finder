import numpy as np

INPUT_FILE = "DATA.bin"
OUTPUT_FILE = "METAL_MODEL.npz"

PHASES = 64
WAVEFORMS = 1005

COMPONENTS = 8

VALIDATION_RATIO = 0.20
THRESHOLD_PERCENTILE = 99.0

EIGENVALUE_FLOOR = 1e-6


data = np.fromfile(
    INPUT_FILE,
    dtype="<u2"
).astype(np.float32)

expected_samples = (
    WAVEFORMS *
    PHASES
)

print(
    f"File samples:     {len(data)}"
)

print(
    f"Expected samples: {expected_samples}"
)

if len(data) != expected_samples:

    raise ValueError(
        f"Invalid DATA.bin: expected "
        f"{expected_samples} samples, "
        f"but got {len(data)}"
    )

waves = data.reshape(
    WAVEFORMS,
    PHASES
)

np.random.seed(42)

indices = np.random.permutation(
    WAVEFORMS
)

waves = waves[indices]

validation_count = int(
    WAVEFORMS *
    VALIDATION_RATIO
)

train_waves = waves[
    :-validation_count
]

validation_waves = waves[
    -validation_count:
]

mean = np.mean(
    train_waves,
    axis=0
)

centered_train = (
    train_waves -
    mean
)

covariance = np.cov(
    centered_train,
    rowvar=False
)

eigenvalues, eigenvectors = (
    np.linalg.eigh(covariance)
)

order = np.argsort(
    eigenvalues
)[::-1]

eigenvalues = eigenvalues[
    order
]

eigenvectors = eigenvectors[
    :,
    order
]

components = eigenvectors[
    :,
    :COMPONENTS
]

selected_eigenvalues = eigenvalues[
    :COMPONENTS
]

selected_eigenvalues = np.maximum(
    selected_eigenvalues,
    EIGENVALUE_FLOOR
)


def calculate_scores(
    input_waves
):

    centered = (
        input_waves -
        mean
    )

    latent = (
        centered @
        components
    )

    reconstructed = (
        latent @
        components.T
    )

    residual = (
        centered -
        reconstructed
    )

    q_score = np.sum(
        residual * residual,
        axis=1
    )

    t2_score = np.sum(
        (
            latent * latent
        ) /
        selected_eigenvalues,
        axis=1
    )

    return (
        q_score,
        t2_score
    )


train_q, train_t2 = calculate_scores(
    train_waves
)

validation_q, validation_t2 = calculate_scores(
    validation_waves
)

q_threshold = float(
    np.percentile(
        validation_q,
        THRESHOLD_PERCENTILE
    )
)

t2_threshold = float(
    np.percentile(
        validation_t2,
        THRESHOLD_PERCENTILE
    )
)

combined_validation = np.maximum(
    validation_q / max(q_threshold, 1e-12),
    validation_t2 / max(t2_threshold, 1e-12)
)

combined_threshold = float(
    np.percentile(
        combined_validation,
        THRESHOLD_PERCENTILE
    )
)

explained_variance = float(
    np.sum(selected_eigenvalues)
    /
    np.sum(
        np.maximum(
            eigenvalues,
            EIGENVALUE_FLOOR
        )
    )
    * 100.0
)


np.savez(
    OUTPUT_FILE,

    mean=mean.astype(
        np.float32
    ),

    components=components.astype(
        np.float32
    ),

    eigenvalues=selected_eigenvalues.astype(
        np.float32
    ),

    q_threshold=np.float32(
        q_threshold
    ),

    t2_threshold=np.float32(
        t2_threshold
    ),

    combined_threshold=np.float32(
        combined_threshold
    ),

    phases=np.int32(
        PHASES
    ),

    components_count=np.int32(
        COMPONENTS
    )
)


print()
print("MODEL CREATED")
print("-------------")
print(
    f"Output:              {OUTPUT_FILE}"
)
print(
    f"Waveforms:           {WAVEFORMS}"
)
print(
    f"Training:            {len(train_waves)}"
)
print(
    f"Validation:          {len(validation_waves)}"
)
print(
    f"Phases:              {PHASES}"
)
print(
    f"Components:          {COMPONENTS}"
)
print(
    f"Explained variance:  {explained_variance:.4f}%"
)
print(
    f"Q threshold:         {q_threshold:.6f}"
)
print(
    f"T2 threshold:        {t2_threshold:.6f}"
)
print(
    f"Combined threshold:  {combined_threshold:.6f}"
)

print()
print("MEAN:")
print(mean)

print()
print("EIGENVALUES:")
print(selected_eigenvalues)