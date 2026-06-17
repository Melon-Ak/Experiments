# TensorFlow/Keras 花卉分类模型训练与 TFLite 导出实验报告

## 一、实验目的

使用 TensorFlow + Keras 训练一个花卉 5 分类模型（daisy / dandelion / roses / sunflowers / tulips），采用 MobileNetV2 迁移学习，训练完成后转换为 TensorFlow Lite 可部署的 `.tflite` 文件，供 Experiment4 的 Android 端实时图像分类使用。

整个流程不依赖 `tflite-model-maker`（该包与新版 Python/TensorFlow 存在 `scann` 安装冲突），仅用 TensorFlow 标准 API 完成。

***

## 二、实验环境

- **操作系统**：Windows 10/11
- **编程语言**：Python 3.10 / 3.11
- **深度学习框架**：TensorFlow 2.15+
- **辅助库**：matplotlib 3.7+、numpy 1.23+
- **预训练模型**：MobileNetV2（ImageNet 权重）
- **训练数据**：TensorFlow 官方 flower_photos 数据集（3670 张，5 类）
- **实验教程**：[CSDN - TensorFlow 花卉分类教程](https://blog.csdn.net/llfjfz/article/details/161630612)

***

## 三、实验步骤

### 3.1 环境安装与配置

安装 TensorFlow 及相关依赖库，确保 Python 环境中具备模型训练所需的所有包。

**实验注解：**
- **核心操作**：使用 `pip install tensorflow matplotlib numpy`
- **技术要点**：TensorFlow 安装包较大，建议使用国内镜像源（如清华镜像）加速下载
- **注意事项**：建议使用 Python 3.10 或 3.11，TensorFlow 2.15+ 对这两个版本支持最好

**依赖文件（requirements-modern.txt）：**

```text
tensorflow>=2.15
matplotlib>=3.7
numpy>=1.23
```

### 3.2 数据集准备与划分

使用 TensorFlow 官方花卉数据集 `flower_photos.tgz`，自动下载并解压。数据集按 **80:10:10** 比例划分为训练集、验证集和测试集。

**实验注解：**
- **对应代码**：`train_flower_classifier.py` 中的 `load_flower_datasets()` 函数
- **核心操作**：使用 `tf.keras.utils.image_dataset_from_directory` 自动识别子文件夹为类别标签
- **技术要点**：数据管道开启 `cache().shuffle().prefetch()` 减少 I/O 等待，提升训练效率

**数据集结构：**

```
flower_photos/
├── daisy/       (633 张)
├── dandelion/   (898 张)
├── roses/       (641 张)
├── sunflowers/  (699 张)
└── tulips/      (799 张)
```

### 3.3 构建 MobileNetV2 迁移学习模型

基于 ImageNet 预训练的 MobileNetV2 构建迁移学习模型，冻结基础网络，仅训练最后的分类层。

**实验注解：**
- **对应代码**：`train_flower_classifier.py` 中的 `build_model()` 函数
- **模型架构**：输入(224×224×3) → MobileNetV2 预处理 → MobileNetV2 基础网络(冻结) → GlobalAveragePooling → Dropout(0.2) → Dense(5, softmax)
- **技术要点**：迁移学习利用 ImageNet 预训练的通用特征提取能力，在少量数据上也能获得较好效果

**模型结构：**

```
输入 (224×224×3)
  └─ mobilenet_v2.preprocess_input
       └─ MobileNetV2(weights=imagenet, include_top=False, pooling=avg)  ← 冻结
            └─ Dropout(0.2)
                 └─ Dense(5, softmax)  ← 仅训练这一层
输出 (5 类概率)
```

### 3.4 模型训练

使用 Adam 优化器（学习率 0.001）和 SparseCategoricalCrossentropy 损失函数，训练 5 个 epoch。

**实验注解：**
- **对应代码**：`train_flower_classifier.py` 主流程
- **训练参数**：EPOCHS=5, BATCH_SIZE=32, LEARNING_RATE=1e-3, IMAGE_SIZE=224
- **训练方式**：CPU 训练

**训练过程示例：**

| Epoch | Loss | Accuracy | Val Loss | Val Accuracy |
|-------|------|----------|----------|-------------|
| 1/5   | 0.7762 | 74.24% | 0.3824 | 89.60% |
| 2/5   | 0.3344 | 89.05% | 0.2714 | 91.28% |
| 3/5   | 0.2514 | 91.28% | 0.2283 | 92.10% |
| 4/5   | 0.2037 | 92.65% | 0.2045 | 93.50% |
| 5/5   | 0.1726 | 93.45% | 0.1926 | 94.35% |

**测试集评估：** test_loss ≈ 0.19, test_accuracy ≈ 94%

### 3.5 TFLite 模型转换与量化

将训练好的 Keras 模型转换为 TensorFlow Lite 格式，并应用动态范围量化以减小模型体积。

**实验注解：**
- **对应代码**：`train_flower_classifier.py` 中的 `convert_to_tflite()` 函数
- **量化方式**：dynamic range quantization（动态范围量化）
- **技术要点**：TFLite 转换后模型约 2.5MB，适合移动端部署

**量化模式对比：**

| 模式 | 特点 | 体积 |
|------|------|------|
| dynamic（本实验选用） | 权重动态量化，兼容性最好 | ~2.5MB |
| float16 | 半精度浮点，GPU delegate 友好 | ~4.7MB |
| int8 | 全整数量化，需校准数据 | ~2.4MB |
| none | 不量化，调试用 | ~9.3MB |

### 3.6 TFLite 模型测试（Smoke Test）

使用 `tf.lite.Interpreter` 加载导出的 `.tflite` 模型，取测试集图片进行推理验证。

**实验注解：**
- **对应代码**：`train_flower_classifier.py` 中的 `smoke_test_tflite()` 函数
- **核心操作**：加载 TFLite 模型 → 分配张量 → 逐张推理 → 比对预测与真实标签
- **测试结果**：模型能正常加载、推理流程跑通

**Smoke Test 示例输出：**

```
真实=daisy,      预测=daisy
真实=roses,      预测=roses
真实=sunflowers,预测=sunflowers
真实=tulips,     预测=tulips
真实=dandelion,  预测=dandelion
```

**导出文件清单：**

| 文件 | 说明 |
|------|------|
| `exported_flower_model/model.tflite` | TFLite 量化模型（~2.5MB） |
| `exported_flower_model/flower_classifier.keras` | Keras 完整模型（~9.3MB） |
| `exported_flower_model/labels.txt` | 5 类标签文件 |

### 3.7 在 Experiment4 中部署测试

将训练好的 `model.tflite` 复制到 Experiment4 的 Android 项目中，通过 ML Model Binding 自动绑定，实现移动端实时图像分类。

**实验注解：**
- **复制路径**：`exported_flower_model/model.tflite` → `Experiment4/start/src/main/ml/FlowerModel.tflite`
- **绑定机制**：ML Model Binding 在 Gradle Sync 时自动生成 `FlowerModel.kt`，无需手写
- **代码调用**：`flowerModel.process(tfImage)` 直接推理，返回各类别概率
- **验证方法**：USB 真机运行，相机对准花朵，RecyclerView 显示 Top-3 识别结果

**部署流程图：**

```
Experiment5.1（本实验）                    Experiment4（Android 端）
训练 MobileNetV2 → model.tflite   →   放到 start/src/main/ml/FlowerModel.tflite
放到 exported_flower_model/                    ↓
                              ML Model Binding 自动生成 FlowerModel.kt
                              CameraX analyze 回调中推理 + Top-K 排序
                              RecyclerView 展示识别结果
```

***

## 四、实验总结

通过本次实验，完成了从 TensorFlow/Keras 模型训练到 TFLite 模型导出再到 Android 端部署的完整流程，掌握了迁移学习、模型量化和移动端部署的核心技能。

### 实验收获

| 步骤 | 知识点 | 技能提升 |
|------|--------|----------|
| 环境配置 | TensorFlow 安装与配置 | 掌握深度学习环境搭建 |
| 数据准备 | 数据集下载与划分 | 掌握 tf.data 数据管道构建 |
| 模型构建 | MobileNetV2 迁移学习 | 掌握预训练模型微调方法 |
| 模型训练 | Keras 模型训练与评估 | 掌握训练监控与超参调优 |
| 模型导出 | TFLite 转换与量化 | 掌握移动端模型部署准备 |
| Smoke Test | TFLite 推理验证 | 掌握模型部署前验证方法 |
| 端侧部署 | ML Model Binding + CameraX | 掌握 Android 端 TFLite 集成 |

### 重点难点

- **迁移学习**：理解冻结基础网络、仅训练分类层的原理和优势
- **模型量化**：掌握 dynamic/float16/int8 三种量化模式的区别和适用场景
- **端侧部署**：理解 `.tflite` 文件在 Android 端通过 ML Model Binding 自动绑定的工作流程

### 代码文件清单

| 文件路径 | 功能描述 |
|----------|----------|
| `exported_flower_model/model.tflite` | TFLite 量化模型（2.5MB），用于 Android 部署 |
| `exported_flower_model/flower_classifier.keras` | Keras 完整模型，可继续训练 |
| `exported_flower_model/labels.txt` | 5 类标签文件 |
| `Experiment4/start/src/main/ml/FlowerModel.tflite` | 已部署到 Android 端的模型副本 |
| `experiment5.1.md` | 本实验报告 |

***

## 五、参考资料

- TensorFlow Lite Converter 官方文档：https://ai.google.dev/edge/litert/conversion/tensorflow/convert_tf
- MobileNetV2（Keras）：https://keras.io/api/applications/mobilenet/
- TensorFlow 花卉分类教程（CSDN）：https://blog.csdn.net/llfjfz/article/details/161630612
- TensorFlow Flowers 官方数据集：https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz
