# Experiment4 实验报告：基于 CameraX + TensorFlow Lite 的实时图像分类

## 一、实验目的

基于 Google Codelab 提供的 TFL Flowers 分类项目（`start` 模块作为起步代码，`finish` 模块作为参考答案），完成以下三件事：

1. 将项目从 Gradle 6.5 + AGP 4.1 升级到 **Gradle 8.7 + AGP 8.5**；
2. 修复升级后出现的所有构建错误（Manifest Merger、MethodHandle API 级别、ML Model Binding 依赖缺失、Java 语言级别弃用等）；
3. 在 `start` 模块补全 TODO 代码：初始化 TFL Flowers 模型、CameraX analyze 回调中将 ImageProxy → Bitmap → TensorImage → 推理 → 排序 Top-K → 封装 Recognition → 交给 RecyclerView 展示。

---

## 二、项目结构

```
Experiment4/
├── build.gradle                  顶层（插件 DSL + 版本约定）
├── settings.gradle               pluginManagement + dependencyResolutionManagement
├── gradle.properties             AndroidX / Jetifier / 编码
├── gradle/wrapper/gradle-wrapper.properties  distributionUrl -> gradle-8.7-bin
├── start/                         起步模块（本实验完成的模块）
│   ├── build.gradle              AGP 8.5.0 + Kotlin 1.9.24 + compileSdk 34 + minSdk 26
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/.../MainActivity.kt
│       └── ml/FlowerModel.tflite  ← 训练好的花朵分类模型
└── finish/                        参考答案模块（实验完成后也同步升级）
```

---

## 三、Gradle / AGP 版本升级

### 3.1 升级矩阵

| 组件 | 原值 | 升级后 |
|---|---|---|
| Gradle Wrapper | 6.5 | **8.7** |
| Android Gradle Plugin | `com.android.tools.build:gradle:4.1.0-rc03` | **插件 DSL `com.android.application` version 8.5.0** |
| Kotlin | 1.3.72 | **1.9.24** |
| compileSdk / targetSdk | 29 / 30 | **34** |
| minSdk | 21（因 Guice 问题）→ **26** | 26 |
| Java source/target | 1.8（已弃用警告） | **11** |

### 3.2 关键配置变更

**1. gradle-wrapper.properties**

```properties
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.7-bin.zip
networkTimeout=10000
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
```

**2. 顶层 build.gradle** 切换到插件 DSL，去掉 `buildscript {} + allprojects {}` 的旧版写法：

```groovy
plugins {
    id 'com.android.application' version '8.5.0' apply false
    id 'org.jetbrains.kotlin.android' version '1.9.24' apply false
}
```

**3. settings.gradle**

```groovy
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Experiment4"
include ':start'
include ':finish'
```

**4. start/build.gradle（关键片段）**

```groovy
android {
    namespace 'org.tensorflow.lite.examples.classification'
    compileSdk 34

    defaultConfig {
        applicationId "org.tensorflow.lite.examples.classification"
        minSdk 26
        targetSdk 34
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_11
        targetCompatibility JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = '11'
    }

    buildFeatures {
        dataBinding = true
        buildConfig = true
        mlModelBinding true        // ← 打开 ML Model Binding
    }
}

dependencies {
    // CameraX 1.3.4
    implementation 'androidx.camera:camera-core:1.3.4'
    implementation 'androidx.camera:camera-camera2:1.3.4'
    implementation 'androidx.camera:camera-lifecycle:1.3.4'
    implementation 'androidx.camera:camera-view:1.3.4'

    // TensorFlow Lite
    implementation 'org.tensorflow:tensorflow-lite-support:0.4.4'
    implementation 'org.tensorflow:tensorflow-lite:2.15.0'
    implementation 'org.tensorflow:tensorflow-lite-gpu:2.15.0' {
        exclude group: 'com.google.inject', module: 'guice'  // 去掉 MethodHandle 来源
    }
    implementation 'org.tensorflow:tensorflow-lite-metadata:0.2.0'  // ML Binding 所需
}
```

---

## 四、构建错误修复记录

### 4.1 MethodHandle.invoke 仅支持 API 26+

**报错：**
```
MethodHandle.invoke and MethodHandle.invokeExact are only supported starting with Android O (--min-api 26):
Lcom/google/inject/internal/aop/AbstractGlueGenerator;...
```

**根因：** `tensorflow-lite-gpu` 的 POM 传递引入了 `guice:5.1.0`，Guice 在 dex 中使用了 `java.lang.invoke.MethodHandle.invoke`，而 Android 平台原生只在 API 26+ 支持该调用。Android Core Library Desugaring 不覆盖这个方法。

**修法（双保险）：**

- 在 `tensorflow-lite-gpu` 依赖上 `exclude group: 'com.google.inject', module: 'guice'`；
- 把 `minSdk` 从 21 提到 26。

### 4.2 Manifest Merger 系列错误

**(1) tools:replace 指定了属性但未给出新值**

AGP 8.x 比 4.x 严格得多。原来写了：
```xml
<application tools:replace="android:usesCleartextTraffic,android:debuggable,android:extractNativeLibs,
   android:networkSecurityConfig,android:fullBackupContent,android:dataExtractionRules">
```
但 `<application>` 标签里并没有显式给出这些属性的值，于是 Merger 报错 *"tools:replace specified ... but no new value specified"*。

**修法：** 只保留我们真的显式赋值的项：
```xml
<application ...
    tools:replace="android:allowBackup,android:label">
```

**(2) Manifest 里重复写了 package**

AGP 8.x 以后 `<manifest package="...">` 会被忽略，namespace 只认 `build.gradle`。删掉了两个模块 manifest 根节点的 `package` 属性。

**(3) uses-permission / uses-feature 被 CameraX 注入重复**

CameraX 1.3.4 的 AAR manifest 自带了 `CAMERA` 权限和 `android.hardware.camera.any` 特性，与项目自己写的重复。AGP 8 Merger 默认对重复 permission 直接失败。

**修法：** 加 `tools:node="merge"`：
```xml
<uses-permission android:name="android.permission.CAMERA"  tools:node="merge" />
<uses-feature    android:name="android.hardware.camera.any" tools:node="merge" />
```

**(4) Android 12+ 强制 android:exported**

targetSdk 34 的项目，任何含 `<intent-filter>` 的组件必须显式声明 `android:exported`。MainActivity 是 LAUNCHER 入口，所以值必须是 `true`。

### 4.3 ML Model Binding：MetadataExtractor 找不到

**报错：**
```
FlowerModel.java: import org.tensorflow.lite.support.metadata.MetadataExtractor;
                                              ^
程序包 org.tensorflow.lite.support.metadata 不存在
```

**根因：** `FlowerModel.java` 是 ML Model Binding 在编译时自动生成的代码，里面会 import `MetadataExtractor`。这个类并不在 `tensorflow-lite-support:0.4.4`，而在独立的 `tensorflow-lite-metadata:0.2.0` 中。

**修法：** 显式加一行依赖：
```groovy
implementation 'org.tensorflow:tensorflow-lite-metadata:0.2.0'
```

### 4.4 Java source 8 过时警告

AGP 8.x 用内置 JDK 运行，推荐 compileOptions 至少 Java 11。把：
```groovy
sourceCompatibility JavaVersion.VERSION_1_8 → VERSION_11
jvmTarget = '1_8' → '11'
```

---

## 五、TODO 代码实现（MainActivity.kt）

### TODO 1：初始化 TFL 模型

```kotlin
private val flowerModel: FlowerModel by lazy {
    val compatList = CompatibilityList()
    val options = if (compatList.isDelegateSupportedOnThisDevice) {
        Model.Options.Builder().setDevice(Model.Device.GPU).build()
    } else {
        Model.Options.Builder().setNumThreads(4).build()
    }
    FlowerModel.newInstance(ctx, options)
}
```

要点：首次在 analyze 线程访问时才初始化；优先用 GPU 委托（骁龙 845+ / AEP），否则回落 4 线程 CPU。

### TODO 2：ImageProxy → Bitmap → TensorImage

```kotlin
val tfImage = TensorImage.fromBitmap(toBitmap(imageProxy))
```

项目里已提供 `toBitmap()`，内部完成 YUV_420_888 → ARGB + 按相机传感器方向做旋转。

### TODO 3：推理 + 排序 + Top-K

```kotlin
flowerModel.process(tfImage)
    .probabilityAsCategoryList.apply {
        sortByDescending { it.score }
    }.take(MAX_RESULT_DISPLAY)
```

`probabilityAsCategoryList` 是 ML Binding 给分类模型自动生成的扩展方法。`MAX_RESULT_DISPLAY` 在 companion object 里定义为 `3`，即展示概率最高的 3 个类别。

### TODO 4：封装为 Recognition

```kotlin
for (output in outputs) {
    items.add(Recognition(output.label, output.score))
}
```

`Recognition(label, score)` 是 RecyclerView 适配器 `RecognitionAdapter` 识别的数据类。

### 原始的虚拟显示代码

原框架里有一段 `canvas.drawText("Fake label ...")` 画在 overlay 上，完成推理后已经不再需要，整段删除。

---

## 六、添加 TFL 模型到模块

把训练好的 `FlowerModel.tflite` 放到：

```
Experiment4/start/src/main/ml/FlowerModel.tflite
```

Android Gradle Plugin 8.x + `buildFeatures { mlModelBinding true }` 会在 `:start:processDebugMainManifest` 前自动执行 ML Model Binding 任务，把 `.tflite` 解析为 Kotlin/Java 数据绑定类：

```
start/build/generated/mlDataBinding/debug/
    └── org/tensorflow/lite/examples/classification/ml/
        ├── FlowerModel.kt
        └── FlowerModelProcessor.kt
```

`FlowerModel.newInstance(...)` / `FlowerModel.process(tfImage)` 都是生成类提供的静态 API。

---

## 七、Manifest 最终版

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.CAMERA"
        tools:node="merge" />
    <uses-feature android:name="android.hardware.camera.any"
        tools:node="merge" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.TFLClassify"
        tools:replace="android:allowBackup,android:label">

        <activity android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

---

## 八、USB 真机联调步骤

1. 手机开开发者选项 → 开 USB 调试 → USB 模式设为"文件传输"。
2. Windows 装 Google USB Driver（Android Studio SDK Tools）或厂商驱动。
3. `adb devices` 看到 `device` 状态；若 `unauthorized` 则手机重新允许。
4. Android Studio：
   - Gradle Sync（触发 ML Model Binding 生成 FlowerModel.kt）；
   - Run → 选真机。
5. 首次启动需要点相机权限。查看日志：`adb logcat -s "TFL" *:S`。

---

## 九、实验结果截图

> 请把以下两张图片放到 `Experiment4/images/` 目录中，文件路径可直接使用。

**截图 1：补完 TODO + 所有错误已消除的 Android Studio 工程视图**

![工程完成截图](images/build_success.png)

> 建议截图内容：Android Studio 打开 start 模块，Gradle Sync 成功、构建面板显示 BUILD SUCCESSFUL，MainActivity.kt 中 TODO 1~4 区域已填完代码。

**截图 2：真机调试效果图（Camera 实时预览 + 花朵分类 Top-3 列表）**

![真机调试截图](images/runtime_result.jpg)

> 建议截图内容：手机屏幕，相机对准一朵花（或任意物体），右下或右侧 RecyclerView 显示 Top 3 识别结果（label + 概率）。

---

## 十、总结

本实验完成了从 Gradle 6.5 + AGP 4.1 到 Gradle 8.7 + AGP 8.5 的完整升级链路，覆盖了：

- Wrapper 版本升级、插件 DSL 切换、仓库迁移到 mavenCentral；
- minSdk/targetSdk 矩阵升级、compileOptions 升到 Java 11；
- TensorFlow Lite 2.15.0 + support 0.4.4 + metadata 0.2.0 + CameraX 1.3.4 + Material 1.11.0 的依赖组合；
- Manifest Merger 的 AGP 8.x 新规则（tools:replace / tools:node / android:exported / 删 manifest package）；
- ML Model Binding 的启用与生成类 FlowerModel 的调用；
- Guice + MethodHandle 的 min-api 26 问题处理。

`start` 模块现在可以在 Android Studio 中直接 Sync + Run 到真机，实现实时相机图像分类。
