# Experiment5 实验报告：TensorFlow/Keras 训练花卉图片分类器并导出 TFLite

## 一、实验目的

使用 **TensorFlow 2.15 + Keras** 训练一个花卉 5 分类模型（daisy / dandelion / roses / sunflowers / tulips），采用 **MobileNetV2 迁移学习**，训练完成后转换为 TensorFlow Lite 可部署的 `.tflite` 文件，供 Experiment4 的 Android 端使用。

整个流程 **不依赖 tflite-model-maker**（该包与新版 Python / 新版 TF 有常见的 `scann` 安装冲突），只用 TensorFlow 即可完成。

---

## 二、环境准备

- Python 3.10 或 3.11（不建议 3.12+，截至 2024 年部分 TF 依赖仍滞后）
- TensorFlow 2.15+
- matplotlib 3.7+、numpy 1.23+

```text
# requirements-modern.txt
tensorflow>=2.15
matplotlib>=3.7
numpy>=1.23
```

数据来源：TensorFlow 官方花卉数据集（flower_photos），第一次运行自动下载到 Keras 缓存目录（Windows 默认在 `C:\Users\你的用户名\.keras\datasets\`）。

```
FLOWER_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
```

解压后目录结构（每个子文件夹 = 一个类别）：

```
flower_photos/
├── daisy/       (633 张)
├── dandelion/   (898 张)
├── roses/       (641 张)
├── sunflowers/  (699 张)
└── tulips/      (799 张)
```

也可以把自己的图片按相同目录结构放到 `DATA_DIR` 下。

---

## 三、训练与导出完整代码

```python
import tarfile
from pathlib import Path

import numpy as np
import tensorflow as tf

FLOWER_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
print("TensorFlow 版本:", tf.__version__)

DATA_DIR = None                         # None = 自动下载官方数据集；或 r"D:\path\to\my_images"
EXPORT_DIR = "exported_flower_model"   # 导出目录
EPOCHS = 5
BATCH_SIZE = 32
IMAGE_SIZE = 224
LEARNING_RATE = 1e-3
QUANTIZATION = "dynamic"                # dynamic / float16 / int8 / none
SEED = 123


# -------- 1. 读取并划分数据集 --------
def load_flower_datasets(data_dir, image_size, batch_size, seed):
    if data_dir is None:
        archive_path = tf.keras.utils.get_file(
            "flower_photos.tgz", FLOWER_URL, extract=False,
        )
        archive_path = Path(archive_path)

        candidates = [
            archive_path.parent / "flower_photos",
            archive_path.parent / "flower_photos_extracted" / "flower_photos",
        ]
        data_dir = next((p for p in candidates if p.exists()), None)
        if data_dir is None:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(archive_path.parent / "flower_photos_extracted")
            data_dir = archive_path.parent / "flower_photos_extracted" / "flower_photos"
    else:
        data_dir = Path(data_dir)

    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training",
        seed=seed, image_size=(image_size, image_size), batch_size=batch_size,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation",
        seed=seed, image_size=(image_size, image_size), batch_size=batch_size,
    )
    class_names = train_ds.class_names

    val_batches = int(tf.data.experimental.cardinality(val_ds).numpy())
    test_ds = val_ds.take(val_batches // 2)
    val_ds  = val_ds.skip(val_batches // 2)

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000, seed=seed).prefetch(autotune)
    val_ds   = val_ds.cache().prefetch(autotune)
    test_ds  = test_ds.cache().prefetch(autotune)
    return train_ds, val_ds, test_ds, class_names


# -------- 2. 构建 MobileNetV2 迁移学习模型 --------
def build_model(num_classes, image_size, learning_rate):
    inputs = tf.keras.Input(shape=(image_size, image_size, 3), name="image")
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(image_size, image_size, 3),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )
    base_model.trainable = False
    x = base_model(x, training=False)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="predictions",
    )(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model


# -------- 3. TFLite 转换 --------
def convert_to_tflite(model, quantization, representative_ds):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    if quantization == "dynamic":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    elif quantization == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    elif quantization == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        def representative_data_gen():
            for images, _ in representative_ds.take(100):
                for image in images:
                    yield [tf.expand_dims(tf.cast(image, tf.float32), 0)]

        converter.representative_dataset = representative_data_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type  = tf.uint8
    elif quantization != "none":
        raise ValueError(f"Unsupported quantization mode: {quantization}")

    return converter.convert()


# -------- 4. TFLite 快速测试 --------
def smoke_test_tflite(tflite_path, test_ds, class_names):
    interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    input_details  = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]

    images, labels = next(iter(test_ds.unbatch().batch(8)))
    input_data = tf.cast(images, input_details["dtype"]).numpy()

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
    for expected, predicted in zip(labels.numpy()[:5], predicted_ids[:5]):
        print(f"真实={class_names[expected]}, 预测={class_names[predicted]}")


# ========== 主流程 ==========
train_ds, val_ds, test_ds, class_names = load_flower_datasets(
    DATA_DIR, IMAGE_SIZE, BATCH_SIZE, SEED,
)
print("类别数量:", len(class_names))
print("类别名称:", class_names)

model = build_model(len(class_names), IMAGE_SIZE, LEARNING_RATE)
model.summary()

history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)

loss, accuracy = model.evaluate(test_ds)
print(f"test_loss={loss:.4f}, test_accuracy={accuracy:.4f}")

export_dir = Path(EXPORT_DIR)
export_dir.mkdir(parents=True, exist_ok=True)

(export_dir / "labels.txt").write_text(
    "\n".join(class_names) + "\n", encoding="utf-8",
)
model.save(export_dir / "flower_classifier.keras")

tflite_model = convert_to_tflite(model, QUANTIZATION, train_ds)
(export_dir / "model.tflite").write_bytes(tflite_model)

print("=== 导出文件 ===")
for name in ["labels.txt", "flower_classifier.keras", "model.tflite"]:
    print("  ", export_dir / name)

print("\n=== TFLite Smoke Test ===")
smoke_test_tflite(export_dir / "model.tflite", test_ds, class_names)
```

---

## 四、执行步骤说明

### 4.1 数据集划分

`load_flower_datasets` 完成三件事：

1. 若 `DATA_DIR is None`，用 `tf.keras.utils.get_file` 下载官方 `flower_photos.tgz`，再用 `tarfile` 解压；
2. `image_dataset_from_directory` 会自动把每个子目录名作为一个类别（`class_names`）；
3. 原始 validation_split=0.2 的那 20% 再对半分，得到 **训练 : 验证 : 测试 = 80 : 10 : 10**。

数据管道开启了 `cache().shuffle().prefetch()`，减少 GPU 等待数据。

### 4.2 迁移学习（MobileNetV2）

```
输入 (224×224×3)
  └─ mobilenet_v2.preprocess_input
       └─ MobileNetV2(weights=imagenet, include_top=False, pooling=avg)  ← 冻结
            └─ Dropout(0.2)
                 └─ Dense(5, softmax)  ← 仅训练这一层
输出 (5)
```

- MobileNetV2 是 ImageNet 预训练的，能提图像边缘/纹理/形状等通用特征；
- `base_model.trainable = False` 冻结，**只训练最后的 Dense 分类层**；
- 训练数据少时迁移学习效果远好于从零训练。

### 4.3 TFLite 转换与量化

| 模式 | 特点 | 建议 |
|---|---|---|
| `dynamic` | 默认；权重动态量化；无需校准数据；兼容性最好 | **推荐** |
| `float16` | 半精度浮点数；模型更小；GPU delegate 友好 | 手机 GPU 可用 |
| `int8` | 全整数量化；体积最小；需要 representative_data_gen 校准 | 部署体积最敏感时 |
| `none` | 不量化 | 调试用 |

转换后得到 `model.tflite`（本 Experiment4 Android 端最终需要的就是这个文件，配合 ML Model Binding 使用时文件名要改成 `FlowerModel.tflite` 放在 `app/src/main/ml/` ）。

### 4.4 Smoke Test

用 `tf.lite.Interpreter` 直接加载 `.tflite`，取 8 张测试图片跑推理；int8 模型按 quantization scale/zero_point 把 float 输入转成 uint8。

---

## 五、实验结果

在官方 flower_photos 数据集（3670 张，5 类）上训练 5 个 epoch：

```
训练过程示例（CPU，约 2 min / epoch）：
Epoch 1/5  loss: 0.7762  accuracy: 0.7424  val_loss: 0.3824  val_accuracy: 0.8960
Epoch 2/5  loss: 0.3344  accuracy: 0.8905  val_loss: 0.2714  val_accuracy: 0.9128
...
test_loss = 0.1926, test_accuracy = 0.9435
```

Smoke Test 示例输出：
```
真实=daisy,      预测=daisy
真实=roses,      预测=roses
真实=sunflowers,预测=sunflowers
...
```

导出文件：

```
exported_flower_model/
├── model.tflite          ← 给 Android 用（要改名为 FlowerModel.tflite）
├── flower_classifier.keras ← 可继续训练
└── labels.txt            ← 5 行，对应 5 个类别
```

## 六、和 Experiment4 的衔接

```
Experiment5（本实验）                   Experiment4（Android 端）
训练 MobileNetV2 → model.tflite   →   放到 start/src/main/ml/FlowerModel.tflite
放到 exported_flower_model/                  ↓
                                ML Model Binding 自动生成 FlowerModel.kt
                                CameraX analyze 里推理 + 排序 Top-K
```

如果 Experiment4 需要重新训练（比如换成 17 类 Oxford Flowers），只要：
1. 把 `DATA_DIR` 指向自己的图片目录；
2. `IMAGE_SIZE`、`EPOCHS` 改大；
3. 重新导出 `.tflite` → 覆盖 Android 端的文件 → 真机重新运行。

## 七、参考资料

- TensorFlow Lite Converter 官方文档  
  https://ai.google.dev/edge/litert/conversion/tensorflow/convert_tf
- MobileNetV2（Keras）  
  https://keras.io/api/applications/mobilenet/
- 本实验原教程（CSDN）  
  https://blog.csdn.net/llfjfz/article/details/161630612
