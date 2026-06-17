"""
Experiment 5: TensorFlow/Keras 花卉图片分类器训练与 TFLite 导出
基于 CSDN 教程: https://blog.csdn.net/llfjfz/article/details/161630612

使用 MobileNetV2 迁移学习训练 5 类花卉分类模型，
并导出为 TensorFlow Lite (.tflite) 文件供 Android 端使用。
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import tarfile
from pathlib import Path
import os

import numpy as np
import tensorflow as tf

# ============================================================
# 配置参数
# ============================================================
FLOWER_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"

DATA_DIR = None                         # None = 自动下载官方数据集
EXPORT_DIR = "exported_flower_model"    # 导出目录
EPOCHS = 5
BATCH_SIZE = 32
IMAGE_SIZE = 224
LEARNING_RATE = 1e-3
QUANTIZATION = "dynamic"                # dynamic / float16 / int8 / none
SEED = 123

print("=" * 60)
print("  实验5: TensorFlow/Keras 花卉分类器训练")
print("=" * 60)
print(f"TensorFlow 版本: {tf.__version__}")
print(f"训练轮数: {EPOCHS}")
print(f"批次大小: {BATCH_SIZE}")
print(f"图片尺寸: {IMAGE_SIZE}x{IMAGE_SIZE}")
print(f"量化方式: {QUANTIZATION}")
print(f"导出目录: {EXPORT_DIR}")
print("=" * 60)


# ============================================================
# 1. 读取并划分数据集
# ============================================================
def load_flower_datasets(data_dir, image_size, batch_size, seed):
    """加载花卉数据集，按 80:10:10 划分训练/验证/测试集"""
    if data_dir is None:
        archive_path = tf.keras.utils.get_file(
            "flower_photos.tgz",
            FLOWER_URL,
            extract=False,
        )
        archive_path = Path(archive_path)

        # 检查是否已解压
        candidates = [
            archive_path.parent / "flower_photos",
            archive_path.parent / "flower_photos_extracted" / "flower_photos",
        ]
        data_dir = next((path for path in candidates if path.exists()), None)
        if data_dir is None:
            print("正在解压数据集...")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(archive_path.parent / "flower_photos_extracted")
            data_dir = archive_path.parent / "flower_photos_extracted" / "flower_photos"
            print(f"数据集已解压到: {data_dir}")
    else:
        data_dir = Path(data_dir)

    # 从目录加载图片
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=seed,
        image_size=(image_size, image_size),
        batch_size=batch_size,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=seed,
        image_size=(image_size, image_size),
        batch_size=batch_size,
    )
    class_names = train_ds.class_names

    # 将验证集再分成验证集和测试集 (各10%)
    val_batches = int(tf.data.experimental.cardinality(val_ds).numpy())
    test_ds = val_ds.take(val_batches // 2)
    val_ds = val_ds.skip(val_batches // 2)

    # 数据管道优化
    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000, seed=seed).prefetch(autotune)
    val_ds = val_ds.cache().prefetch(autotune)
    test_ds = test_ds.cache().prefetch(autotune)

    return train_ds, val_ds, test_ds, class_names


# ============================================================
# 2. 构建 MobileNetV2 迁移学习模型
# ============================================================
def build_model(num_classes, image_size, learning_rate):
    """使用 ImageNet 预训练的 MobileNetV2 + 自定义分类头"""
    inputs = tf.keras.Input(shape=(image_size, image_size, 3), name="image")

    # MobileNetV2 预处理
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)

    # 加载预训练模型（不含顶层）
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(image_size, image_size, 3),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )

    # 冻结预训练参数
    base_model.trainable = False
    x = base_model(x, training=False)
    x = tf.keras.layers.Dropout(0.2)(x)

    # 分类输出层
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="predictions"
    )(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


# ============================================================
# 3. TFLite 转换
# ============================================================
def convert_to_tflite(model, quantization, representative_ds):
    """将 Keras 模型转换为 TensorFlow Lite 格式并量化"""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    if quantization == "dynamic":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        print("  使用 dynamic range 量化")
    elif quantization == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        print("  使用 float16 量化")
    elif quantization == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        def representative_data_gen():
            for images, _ in representative_ds.take(100):
                for image in images:
                    yield [tf.expand_dims(tf.cast(image, tf.float32), 0)]

        converter.representative_dataset = representative_data_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.uint8
        print("  使用 int8 全整数量化")
    elif quantization == "none":
        print("  不量化，保留浮点模型")
    else:
        raise ValueError(f"不支持的量化方式: {quantization}")

    return converter.convert()


# ============================================================
# 4. TFLite 快速测试 (Smoke Test)
# ============================================================
def smoke_test_tflite(tflite_path, test_ds, class_names):
    """使用 TFLite Interpreter 快速验证模型推理"""
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    print(f"  输入类型: {input_details['dtype']}, 形状: {input_details['shape']}")
    print(f"  输出类型: {output_details['dtype']}, 形状: {output_details['shape']}")

    # 取测试集前 8 张图片做快速推理
    images, labels = next(iter(test_ds.unbatch().batch(8)))
    input_data = tf.cast(images, input_details["dtype"]).numpy()

    # uint8 量化模型需要特殊处理
    if input_details["dtype"] == np.uint8:
        scale, zero_point = input_details["quantization"]
        if scale:
            input_data = images.numpy() / scale + zero_point
            input_data = np.clip(input_data, 0, 255).astype(np.uint8)

    predictions = []
    for image in input_data:
        interpreter.set_tensor(input_details["index"], np.expand_dims(image, 0))
        interpreter.invoke()
        predictions.append(interpreter.get_tensor(output_details["index"])[0])

    predicted_ids = np.argmax(np.asarray(predictions), axis=1)

    print("\n  Smoke Test 结果 (前5张):")
    correct = 0
    for i, (expected, predicted) in enumerate(
        zip(labels.numpy()[:5], predicted_ids[:5])
    ):
        match = "✓" if expected == predicted else "✗"
        print(f"    [{match}] 真实={class_names[expected]:12s} 预测={class_names[predicted]}")
        if expected == predicted:
            correct += 1
    print(f"  Smoke Test 准确率: {correct}/5")


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    print("\n[1/5] 加载数据集...")
    train_ds, val_ds, test_ds, class_names = load_flower_datasets(
        DATA_DIR, IMAGE_SIZE, BATCH_SIZE, SEED,
    )
    print(f"  类别数量: {len(class_names)}")
    print(f"  类别名称: {class_names}")

    # 计算各数据集大小
    train_count = int(tf.data.experimental.cardinality(train_ds).numpy()) * BATCH_SIZE
    val_count = int(tf.data.experimental.cardinality(val_ds).numpy()) * BATCH_SIZE
    test_count = int(tf.data.experimental.cardinality(test_ds).numpy()) * BATCH_SIZE
    print(f"  训练集约: {train_count} 张")
    print(f"  验证集约: {val_count} 张")
    print(f"  测试集约: {test_count} 张")

    print("\n[2/5] 构建模型...")
    model = build_model(len(class_names), IMAGE_SIZE, LEARNING_RATE)
    model.summary()

    print("\n[3/5] 开始训练...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        verbose=1,
    )

    # 打印训练历史
    print("\n  训练历史:")
    for epoch in range(EPOCHS):
        print(
            f"  Epoch {epoch+1}/{EPOCHS} - "
            f"loss: {history.history['loss'][epoch]:.4f}, "
            f"accuracy: {history.history['accuracy'][epoch]:.4f}, "
            f"val_loss: {history.history['val_loss'][epoch]:.4f}, "
            f"val_accuracy: {history.history['val_accuracy'][epoch]:.4f}"
        )

    print("\n[4/5] 测试集评估...")
    loss, accuracy = model.evaluate(test_ds, verbose=0)
    print(f"  test_loss = {loss:.4f}")
    print(f"  test_accuracy = {accuracy:.4f} ({accuracy*100:.2f}%)")

    print("\n[5/5] 导出模型文件...")
    export_dir = Path(EXPORT_DIR)
    export_dir.mkdir(parents=True, exist_ok=True)

    # 保存标签文件
    labels_path = export_dir / "labels.txt"
    labels_path.write_text("\n".join(class_names) + "\n", encoding="utf-8")
    print(f"  ✓ labels.txt ({len(class_names)} 个类别)")

    # 保存 Keras 模型
    keras_path = export_dir / "flower_classifier.keras"
    model.save(keras_path)
    keras_size = keras_path.stat().st_size
    print(f"  ✓ flower_classifier.keras ({keras_size / 1024 / 1024:.1f} MB)")

    # 转换并保存 TFLite 模型
    print("  正在转换为 TFLite...")
    tflite_model = convert_to_tflite(model, QUANTIZATION, train_ds)
    tflite_path = export_dir / "model.tflite"
    tflite_path.write_bytes(tflite_model)
    tflite_size = tflite_path.stat().st_size
    print(f"  ✓ model.tflite ({tflite_size / 1024:.1f} KB)")

    # 文件清单
    print("\n" + "=" * 60)
    print("  导出文件清单:")
    for name in ["labels.txt", "flower_classifier.keras", "model.tflite"]:
        fpath = export_dir / name
        if fpath.exists():
            size_kb = fpath.stat().st_size / 1024
            print(f"    {export_dir}/{name}  ({size_kb:.1f} KB)")
    print("=" * 60)

    # TFLite Smoke Test
    print("\n  TFLite Smoke Test:")
    smoke_test_tflite(export_dir / "model.tflite", test_ds, class_names)

    print("\n" + "=" * 60)
    print("  实验完成! 模型文件已保存到:", export_dir.absolute())
    print("=" * 60)
