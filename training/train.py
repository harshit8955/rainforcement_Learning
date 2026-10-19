"""Train MobileNetV2 on dataset/train, dataset/validation, and evaluate on test.

Expected folders: dataset/{train,validation,test}/{cats,dogs}
"""
import argparse
import json
from pathlib import Path


def build_generators(tf, root, size, batch):
    preprocessing = tf.keras.applications.mobilenet_v2.preprocess_input
    common = dict(target_size=(size, size), batch_size=batch, class_mode="binary", preprocessing_function=preprocessing)
    train = tf.keras.preprocessing.image.ImageDataGenerator(rotation_range=15, zoom_range=.15, horizontal_flip=True).flow_from_directory(root / "train", shuffle=True, **common)
    validation = tf.keras.preprocessing.image.ImageDataGenerator().flow_from_directory(root / "validation", shuffle=False, **common)
    test = tf.keras.preprocessing.image.ImageDataGenerator().flow_from_directory(root / "test", shuffle=False, **common)
    return train, validation, test


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("dataset"))
    parser.add_argument("--output", type=Path, default=Path("models"))
    parser.add_argument("--epochs", type=int, default=12)
    args = parser.parse_args()
    import tensorflow as tf
    args.output.mkdir(parents=True, exist_ok=True)
    train, validation, test = build_generators(tf, args.dataset, 224, 32)
    base = tf.keras.applications.MobileNetV2(include_top=False, weights="imagenet", input_shape=(224, 224, 3))
    base.trainable = False
    inputs = tf.keras.Input((224, 224, 3))
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(tf.keras.layers.Dropout(.25)(tf.keras.layers.GlobalAveragePooling2D()(base(inputs, training=False))))
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    history = model.fit(train, validation_data=validation, epochs=args.epochs, callbacks=[tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)])
    model.save(args.output / "model.keras")
    with open(args.output / "class_names.json", "w", encoding="utf-8") as file:
        json.dump([name for name, _ in sorted(train.class_indices.items(), key=lambda item: item[1])], file)
    with open("artifacts/training_history.json", "w", encoding="utf-8") as file:
        json.dump({key: [float(value) for value in values] for key, values in history.history.items()}, file)
    print(model.evaluate(test, return_dict=True))


if __name__ == "__main__":
    main()
