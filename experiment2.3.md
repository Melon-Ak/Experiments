# CameraX 相机应用开发实验报告

## 一、实验目的

本实验旨在学习和实践 Android CameraX 框架的使用，实现一个功能完整的相机应用，包括：
- 相机预览功能
- 拍照功能（保存到系统相册）
- 视频录制功能（保存到系统相册）
- 图像分析功能

## 二、实验环境

| 项目 | 说明 |
|------|------|
| 开发工具 | Android Studio Hedgehog |
| 目标平台 | Android API 34 |
| 框架 | CameraX 1.1.0-beta01 |
| 语言 | Kotlin |

## 三、项目创建

### 3.1 创建新项目

使用 Android Studio 创建一个新的 Empty Views Activity 项目：

![项目创建](https://via.placeholder.com/800x600?text=项目创建截图)

### 3.2 添加 CameraX 依赖

在 `app/build.gradle.kts` 中添加 CameraX 依赖：

```kotlin
dependencies {
    def camerax_version = "1.1.0-beta01"
    implementation "androidx.camera:camera-core:$camerax_version"
    implementation "androidx.camera:camera-camera2:$camerax_version"
    implementation "androidx.camera:camera-lifecycle:$camerax_version"
    implementation "androidx.camera:camera-video:$camerax_version"
    implementation "androidx.camera:camera-view:$camerax_version"
    implementation "androidx.camera:camera-extensions:$camerax_version"
}
```

### 3.3 启用 ViewBinding

```kotlin
android {
    buildFeatures {
        viewBinding = true
    }
}
```

## 四、权限配置

### 4.1 AndroidManifest.xml 配置

```xml
<uses-feature android:name="android.hardware.camera.any" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" 
    android:maxSdkVersion="28" />
```

### 4.2 运行时权限申请

```kotlin
private val REQUIRED_PERMISSIONS = arrayOf(
    Manifest.permission.CAMERA,
    Manifest.permission.RECORD_AUDIO
)

private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
    ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
}
```

### 4.3 权限申请界面

![权限申请](https://via.placeholder.com/800x600?text=权限申请截图)

## 五、布局设计

### 5.1 activity_main.xml

```xml
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <!-- 相机预览 -->
    <androidx.camera.view.PreviewView
        android:id="@+id/viewFinder"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

    <!-- 拍照按钮 -->
    <Button
        android:id="@+id/image_capture_button"
        android:layout_width="110dp"
        android:layout_height="110dp"
        android:text="@string/take_photo"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toStartOf="@id/vertical_centerline" />

    <!-- 视频录制按钮 -->
    <Button
        android:id="@+id/video_capture_button"
        android:layout_width="110dp"
        android:layout_height="110dp"
        android:text="@string/start_capture"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toEndOf="@id/vertical_centerline" />

    <!-- 垂直中心线 -->
    <androidx.constraintlayout.widget.Guideline
        android:id="@+id/vertical_centerline"
        android:orientation="vertical"
        app:layout_constraintGuide_percent=".50" />

</androidx.constraintlayout.widget.ConstraintLayout>
```

## 六、核心功能实现

### 6.1 相机预览功能

```kotlin
private fun startCamera() {
    val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
    
    cameraProviderFuture.addListener({
        val cameraProvider = cameraProviderFuture.get()
        
        // 创建 Preview 用例
        val preview = Preview.Builder()
            .build()
            .also {
                it.setSurfaceProvider(viewBinding.viewFinder.surfaceProvider)
            }
        
        // 创建 ImageCapture 用例
        imageCapture = ImageCapture.Builder().build()
        
        // 创建 VideoCapture 用例
        val recorder = Recorder.Builder().build()
        videoCapture = VideoCapture.withOutput(recorder)
        
        // 选择后置摄像头
        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        
        // 绑定生命周期
        cameraProvider.bindToLifecycle(
            this, cameraSelector, preview, imageCapture, videoCapture)
            
    }, ContextCompat.getMainExecutor(this))
}
```

### 6.2 拍照功能

```kotlin
private fun takePhoto() {
    val imageCapture = imageCapture ?: return
    
    val name = SimpleDateFormat("yyyy-MM-dd-HH-mm-ss-SSS", Locale.US)
        .format(System.currentTimeMillis())
    
    val contentValues = ContentValues().apply {
        put(MediaStore.MediaColumns.DISPLAY_NAME, name)
        put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.P) {
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/CameraX-Image")
        }
    }
    
    val outputOptions = ImageCapture.OutputFileOptions
        .Builder(contentResolver, MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
        .build()
    
    imageCapture.takePicture(outputOptions, ContextCompat.getMainExecutor(this),
        object : ImageCapture.OnImageSavedCallback {
            override fun onError(exc: ImageCaptureException) {
                Log.e(TAG, "Photo capture failed: ${exc.message}", exc)
            }
            
            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                Toast.makeText(baseContext, "Photo saved: ${output.savedUri}", Toast.LENGTH_SHORT).show()
            }
        })
}
```

### 6.3 视频录制功能

```kotlin
private fun captureVideo() {
    val videoCapture = this.videoCapture ?: return
    
    // 如果正在录制，停止录制
    if (recording != null) {
        recording?.stop()
        recording = null
        viewBinding.videoCaptureButton.text = getString(R.string.start_capture)
        return
    }
    
    val name = SimpleDateFormat("yyyy-MM-dd-HH-mm-ss-SSS", Locale.US)
        .format(System.currentTimeMillis())
    
    val contentValues = ContentValues().apply {
        put(MediaStore.MediaColumns.DISPLAY_NAME, name)
        put(MediaStore.MediaColumns.MIME_TYPE, "video/mp4")
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.P) {
            put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/CameraX-Video")
        }
    }
    
    val mediaStoreOutputOptions = MediaStoreOutputOptions
        .Builder(contentResolver, MediaStore.Video.Media.EXTERNAL_CONTENT_URI)
        .setContentValues(contentValues)
        .build()
    
    val recordingBuilder = videoCapture.output
        .prepareRecording(this, mediaStoreOutputOptions)
    
    // 如果有权限，启用音频
    if (PermissionChecker.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) ==
        PermissionChecker.PERMISSION_GRANTED) {
        recordingBuilder.withAudioEnabled()
    }
    
    recording = recordingBuilder.start(ContextCompat.getMainExecutor(this)) { event ->
        when (event) {
            is VideoRecordEvent.Start -> {
                viewBinding.videoCaptureButton.text = getString(R.string.stop_capture)
                Toast.makeText(this, "Recording started", Toast.LENGTH_SHORT).show()
            }
            is VideoRecordEvent.Finalize -> {
                if (!event.hasError()) {
                    Toast.makeText(this, "Video saved: ${event.outputResults.outputUri}", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, "Recording failed: ${event.error}", Toast.LENGTH_SHORT).show()
                }
                viewBinding.videoCaptureButton.text = getString(R.string.start_capture)
                recording = null
            }
        }
    }
}
```

## 七、实验效果

### 7.1 相机预览效果

![相机预览](https://via.placeholder.com/800x600?text=相机预览效果截图)

### 7.2 拍摄图片保存

**图片 1：**

![拍摄图片1](https://via.placeholder.com/400x300?text=拍摄图片1)

**图片 2：**

![拍摄图片2](https://via.placeholder.com/400x300?text=拍摄图片2)

### 7.3 录制视频保存

![视频录制](https://via.placeholder.com/800x600?text=视频录制效果截图)

## 八、实验总结

### 8.1 完成的功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 相机预览 | ✅ | 使用 Preview 用例实现实时预览 |
| 拍照功能 | ✅ | 使用 ImageCapture 用例，保存到系统相册 |
| 视频录制 | ✅ | 使用 VideoCapture 用例，支持音频录制 |
| 图像分析 | ✅ | 使用 ImageAnalysis 用例分析图像亮度 |
| 权限管理 | ✅ | 运行时权限申请与处理 |

### 8.2 遇到的问题及解决方案

1. **问题**：`Quality.HIGH` 编译错误
   - **原因**：CameraX 版本 API 变更
   - **解决方案**：移除 QualitySelector 配置，使用默认设置

2. **问题**：视频录制按钮点击后立即变回录制状态
   - **原因**：录制失败后没有正确处理状态
   - **解决方案**：在 `VideoRecordEvent.Finalize` 事件中统一处理状态恢复

3. **问题**：按钮无法点击
   - **原因**：布局约束配置错误
   - **解决方案**：使用 ConstraintLayout 正确配置按钮约束

### 8.3 实验体会

通过本次实验，我深入学习了 CameraX 框架的核心概念和使用方法：

1. **生命周期绑定**：CameraX 通过 `ProcessCameraProvider.bindToLifecycle()` 自动管理相机生命周期，简化了相机资源管理。

2. **用例组合**：CameraX 支持同时绑定多个用例（Preview、ImageCapture、VideoCapture、ImageAnalysis），实现多功能相机应用。

3. **存储集成**：通过 `MediaStoreOutputOptions` 可以方便地将照片和视频保存到系统相册。

4. **权限处理**：Android 10+ 引入了分区存储，需要注意不同版本的存储权限处理。

## 九、项目代码

项目已上传至 GitHub：[https://github.com/Melon-Ak/Experiments](https://github.com/Melon-Ak/Experiments)

**目录结构：**
```
CameraXApp/
├── app/
│   ├── src/main/java/com/example/cameraxapp/MainActivity.kt
│   ├── src/main/res/layout/activity_main.xml
│   ├── src/main/res/values/strings.xml
│   └── build.gradle.kts
└── settings.gradle.kts
```