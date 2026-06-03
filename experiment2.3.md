# CameraX 相机应用开发实验报告

## 一、实验目的

学习和实践 Android CameraX 框架的使用，掌握相机预览、拍照、视频录制等核心功能的实现方法，理解 CameraX 生命周期管理和用例组合机制。

***

## 二、实验环境

- **操作系统**：Windows 10/11
- **开发工具**：Android Studio Hedgehog
- **目标平台**：Android API 34
- **框架**：CameraX 1.1.0-beta01
- **语言**：Kotlin

***

## 三、实验任务

### 任务一：配置 CameraX 开发环境

在 Android Studio 中创建新的 CameraX 项目，配置必要的依赖项和权限声明，为后续功能开发做好准备。

**实验注解：**
- **对应文件**：`CameraXApp/app/build.gradle.kts`、`CameraXApp/app/src/main/AndroidManifest.xml`
- **核心配置**：添加 CameraX 核心依赖（camera-core、camera-camera2、camera-lifecycle、camera-video、camera-view）
- **权限声明**：声明 CAMERA、RECORD_AUDIO、WRITE_EXTERNAL_STORAGE 权限
- **技术要点**：Gradle 依赖管理、AndroidManifest 权限配置、ViewBinding 启用

**项目配置截图：**
![CameraX项目配置](images/project_create.png)

### 任务二：实现相机预览功能

使用 CameraX Preview 用例实现相机实时预览，学习 CameraX 生命周期绑定和相机选择器的使用。

**实验注解：**
- **对应文件**：`CameraXApp/app/src/main/java/com/example/cameraxapp/MainActivity.kt`
- **核心组件**：`ProcessCameraProvider` 管理相机生命周期，`Preview` 用例实现预览，`CameraSelector` 选择后置摄像头
- **技术要点**：相机提供者初始化、生命周期绑定、SurfaceProvider 设置

**相机预览效果：**
![相机预览效果](images/camera_preview.png)

### 任务三：实现拍照功能

使用 CameraX ImageCapture 用例实现拍照功能，将拍摄的照片保存到系统相册。

**实验注解：**
- **对应文件**：`CameraXApp/app/src/main/java/com/example/cameraxapp/MainActivity.kt`
- **核心组件**：`ImageCapture` 用例捕获图像，`MediaStoreOutputOptions` 配置输出路径
- **技术要点**：ContentValues 设置、MediaStore 集成、异步回调处理

**拍摄效果截图：**

**图片 1：**
![拍摄图片1](images/photo_1.png)

**图片 2：**
![拍摄图片2](images/photo_2.png)

### 任务四：实现视频录制功能

使用 CameraX VideoCapture 用例实现视频录制功能，支持音频录制和视频保存。

**实验注解：**
- **对应文件**：`CameraXApp/app/src/main/java/com/example/cameraxapp/MainActivity.kt`
- **核心组件**：`Recorder` 配置录制参数，`VideoCapture` 用例捕获视频，`Recording` 控制录制状态
- **技术要点**：录制状态管理、音频权限检查、视频文件保存

**视频录制效果：**
![视频录制效果](images/video_recording.png)

### 任务五：权限管理与用户交互

实现运行时权限申请，确保应用在使用相机和麦克风前获得用户授权。

**实验注解：**
- **对应文件**：`CameraXApp/app/src/main/java/com/example/cameraxapp/MainActivity.kt`
- **核心功能**：动态权限申请、权限回调处理、权限拒绝提示
- **技术要点**：ActivityCompat.requestPermissions、onRequestPermissionsResult 回调

**权限申请截图：**
![权限申请界面](images/permission_request.png)

***

## 四、实验总结

通过本次实验，系统学习了 CameraX 框架的核心概念和使用方法，成功实现了一个功能完整的相机应用。

### 实验收获

| 任务 | 知识点 | 技能提升 |
|------|--------|----------|
| 任务一 | CameraX 依赖配置、权限声明 | 掌握 Android 项目依赖管理 |
| 任务二 | Preview 用例、生命周期绑定 | 掌握相机预览实现方法 |
| 任务三 | ImageCapture 用例、MediaStore 集成 | 掌握拍照和图片保存 |
| 任务四 | VideoCapture 用例、Recorder 配置 | 掌握视频录制功能 |
| 任务五 | 运行时权限申请、用户交互 | 掌握 Android 权限管理 |

### 代码文件清单

| 文件路径 | 功能描述 | 对应任务 |
|----------|----------|----------|
| `CameraXApp/app/build.gradle.kts` | 项目依赖配置 | 任务一 |
| `CameraXApp/app/src/main/AndroidManifest.xml` | 权限声明 | 任务一、五 |
| `CameraXApp/app/src/main/java/com/example/cameraxapp/MainActivity.kt` | 主活动（预览、拍照、录像） | 任务二、三、四、五 |
| `CameraXApp/app/src/main/res/layout/activity_main.xml` | 界面布局（PreviewView、按钮） | 任务二 |

### 项目代码位置

CameraX 实验项目代码已上传至 GitHub 仓库：[https://github.com/Melon-Ak/Experiments](https://github.com/Melon-Ak/Experiments)

**项目结构：**
```
CameraXApp/
├── app/
│   ├── src/main/java/com/example/cameraxapp/MainActivity.kt
│   ├── src/main/res/layout/activity_main.xml
│   ├── src/main/res/values/strings.xml
│   └── build.gradle.kts
└── settings.gradle.kts
```

您可以通过上述链接查看完整的项目代码实现。

***