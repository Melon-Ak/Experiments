# Experiments — Android 智能开发实验集

> 基于 **Kotlin + CameraX + TensorFlow Lite** 的移动端计算机视觉与深度学习综合实验项目。
> 涵盖从环境搭建、语言基础、Android 原生开发，到移动端 AI 模型部署的完整学习链路。

---

## 📁 项目结构

```
Experiments/
├── Experiment4/                 # Android 项目：CameraX + TFLite 实时花卉分类
│   ├── start/                   # 练习模块（含 TODO 1~4）
│   ├── finish/                  # 完成版
│   └── gradle/wrapper/          # Gradle 8.7 Wrapper
├── CameraXApp/                  # CameraX 示例项目
├── BasicsCodelab/               # Android 基础示例
├── MyFirstKotlinApp/            # 第一个 Kotlin App
├── exported_flower_model/       # Experiment5.1 训练产出的花卉分类模型
├── images/                      # 实验截图
├── experiment1.md               # 实验 1：Anaconda 环境管理
├── experiment2.1.md             # 实验 2.1：Kotlin 基本语法
├── experiment2.2.md             # 实验 2.2：Kotlin Android 开发
├── experiment2.3.md             # 实验 2.3：CameraX 相机应用
├── experiment3.md               # 实验 3：Jupyter Notebook 基础
├── experiment4.md               # 实验 4：CameraX + TensorFlow Lite 实时图像分类
├── experiment5.1.md             # 实验 5.1：Keras 花卉分类模型训练
├── experiment5.2.md             # 实验 5.2：石头剪刀布 CNN 模型训练
└── README.md
```

---

## 🧪 实验总览

| # | 实验名称 | 核心内容 | 技术栈 |
|---|---------|---------|--------|
| **1** | [Anaconda 下载与环境管理](experiment1.md) | 安装 Anaconda、创建虚拟环境、包管理、环境导出与迁移 | Anaconda / Conda / Python |
| **2.1** | [Kotlin 基本语法](experiment2.1.md) | 变量、数据类型、控制流、函数、类、扩展函数、协程基础 | Kotlin / JVM |
| **2.2** | [基于 Kotlin 的 Android 开发](experiment2.2.md) | Activity、Intent、布局 XML、ViewModel、LiveData、Fragment | Kotlin / Android SDK / Jetpack |
| **2.3** | [CameraX 相机应用开发](experiment2.3.md) | Preview、ImageAnalysis、ImageCapture、ML Kit 条码识别 | Kotlin / CameraX / ML Kit |
| **3** | [Jupyter Notebook 基础使用](experiment3.md) | Notebook 操作、Markdown 编辑、代码单元、数据可视化、NumPy/Pandas 基础 | Jupyter / Python / NumPy / Pandas / Matplotlib |
| **4** | [CameraX + TensorFlow Lite 实时图像分类](experiment4.md) | ML Model Binding、ImageProxy→Bitmap→TensorImage、GPU/CPU 委托、Top-K 识别 | Kotlin / CameraX / TFLite / Material |
| **5.1** | [Keras 花卉分类模型训练与 TFLite 导出](experiment5.1.md) | MobileNetV2 迁移学习、3 种量化对比、TFLite 导出、Smoke Test | Python / TF 2.x / Keras / TFLite Converter |
| **5.2** | [石头剪刀布 CNN 图像分类](experiment5.2.md) | CNN 4 层卷积、数据增强（7 种）、训练曲线可视化、模型保存 | Python / Keras / Matplotlib |

---

## 🛠 环境要求

### Android 开发（实验 2.2 ~ 2.3、4）

| 工具 | 推荐版本 |
|------|---------|
| Android Studio | Hedgehog 2023.1.1+ 或 Iguana 2024.2+ |
| JDK | 17 或 21 |
| Gradle Wrapper | 8.7（已内置） |
| Android Gradle Plugin | 8.5.0 |
| compileSdk / targetSdk | 34 |
| minSdk | 26（适配 Android 8.0+） |
| Kotlin | 1.9.24 |
| Android SDK Platform | android-34 |
| Build-Tools | 34.0.0 |

### Python / 机器学习（实验 1、3、5.1、5.2）

| 工具 | 推荐版本 |
|------|---------|
| Python | 3.10 ~ 3.11 |
| Anaconda | 2023.11+ 或 Miniconda |
| TensorFlow | 2.15+ |
| Keras | 3.0+ |
| Jupyter | 1.0+ |
| NumPy | 1.24+ |
| Matplotlib | 3.7+ |
| Pillow | 10.0+ |

---

## 🚀 快速开始

### 实验 1：Anaconda 环境管理

```bash
# 下载安装 Anaconda 后
conda create -n exp1 python=3.11
conda activate exp1
pip install numpy pandas matplotlib jupyter
```

### 实验 2.1：Kotlin 基本语法

在 Android Studio 创建 Kotlin Project，或用 IntelliJ IDEA 新建 Kotlin/JVM 工程，逐个实现实验报告中的代码片段。

### 实验 2.2 ~ 2.3：Android 开发

```bash
# 用 Android Studio 打开 CameraXApp 项目
# Run 到真机 / 模拟器
```

### 实验 3：Jupyter Notebook

```bash
jupyter notebook
# 打开 experiment3.md 中的代码段，逐格运行
```

### 实验 4：CameraX + TensorFlow Lite

```bash
cd Experiment4
# Android Studio 打开 start 模块
# Sync → Clean → Rebuild → Run 到真机
```

### 实验 5.1：花卉分类训练

```bash
cd Experiment5.1  # 或直接在 Jupyter 中打开
pip install tensorflow pillow numpy
python train_flower_classifier.py
# 产出 exported_flower_model/model.tflite
```

### 实验 5.2：石头剪刀布训练

```bash
python train_rps.py
# 训练完成后保存 h5 + tflite 版本
```

---

## 📦 模型文件

### Flower 分类（Experiment5.1 产出 → Experiment4 使用）

| 文件 | 大小 | 用途 |
|------|------|------|
| `exported_flower_model/model.tflite` | 2.53 MB | int8 量化花卉分类模型 |
| `exported_flower_model/flower_classifier.keras` | — | Keras 完整模型 |
| `exported_flower_model/labels.txt` | 30 B | 5 类标签 |

**类别：** daisy / dandelion / roses / sunflowers / tulips

**迁移到 Experiment4：**
```bash
copy exported_flower_model\model.tflite Experiment4\start\src\main\ml\FlowerModel.tflite
copy exported_flower_model\model.tflite Experiment4\finish\src\main\ml\FlowerModel.tflite
```

---

## 📸 截图

| 实验 | 截图 |
|------|------|
| 实验 4 — Build 成功 | `images/build_success.png` |
| 实验 4 — 真机运行效果 | `images/runtime_result.jpg` |
| 实验 5.1 — 训练过程 | `images/training_process.png` |
| 实验 5.1 — Smoke Test | `images/tflite_smoke_test.png` |
| 实验 5.2 — 训练曲线 | `images/rps_training_curves.png` |

---

## 🐛 常见问题

### Q1：MethodHandle.invoke only supported starting with Android O？
A：因为 `tensorflow-lite-gpu:2.15.0` 的 POM 里带了 `guice:5.1.0`。解决方案之一：
```groovy
implementation('org.tensorflow:tensorflow-lite-gpu:2.15.0') {
    exclude group: 'com.google.inject', module: 'guice'
}
```
方案二：将 `minSdk` 提到 26。

### Q2：Manifest merger failed（android:exported）？
A：targetSdk 31+ 要求带 `<intent-filter>` 的组件显式声明 `android:exported`：
```xml
<activity
    android:name=".MainActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>
```

### Q3：MetadataExtractor 找不到？
A：ML Model Binding 生成的 `FlowerModel.java` 需要额外依赖：
```groovy
implementation 'org.tensorflow:tensorflow-lite-metadata:0.2.0'
```

### Q4：Android Studio 中 Gradle Sync 卡住？
A：检查 `settings.gradle` 的 `pluginManagement` 和 `dependencyResolutionManagement` 是否包含：
```groovy
google()
mavenCentral()
```

### Q5：真机 USB 连接不上？
1. 打开 USB 调试（开发者选项）
2. USB 模式选「文件传输」
3. `adb devices` 确认设备为 `device` 状态
4. 装 Google USB Driver（SDK Manager → SDK Tools）

---

## 📚 参考资料

- [TensorFlow Lite Android 快速开始](https://developer.android.com/codelabs/tflite-image-classification)
- [CameraX 官方文档](https://developer.android.com/training/camerax)
- [TensorFlow Model Maker](https://www.tensorflow.org/lite/tools/model_maker)
- [Keras 迁移学习](https://keras.io/guides/transfer_learning/)
- [Android 12+ exported 要求](https://developer.android.com/about/versions/12/behavior-changes-12#exported-components)

---

## 📝 License

本项目仅用于教学与实验目的。
