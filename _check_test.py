import importlib
import sys
import subprocess

def check_dependencies():
    print(">>> 正在启动 Sentient Bot V2 环境自检程序...")
    print("-" * 60)

    # 格式: "代码中导入的模块名": "pip安装时的包名"
    requirements = {
        "cv2": "opencv-python",          # 视觉核心
        "numpy": "numpy",                # 矩阵运算
        "mediapipe": "mediapipe",        # 面部网格
        "requests": "requests",          # HTTP 请求 (Ollama)
        "pyttsx3": "pyttsx3",            # 语音合成
        "zmq": "pyzmq",                  # 网络通信 (ZeroMQ)
        "scipy": "scipy",                # 科学计算 (用于生物信号模拟)
        "matplotlib": "matplotlib",      # 绘图库 (虽然目前只用CV2画图，但作为依赖建议保留)
        "yaml": "pyyaml"                 # 配置文件解析 (预留)
    }

    missing = []
    installed = []

    for module_name, package_name in requirements.items():
        try:
            importlib.import_module(module_name)
            # 获取版本号 (有些库版本号属性名不同，简单处理)
            try:
                lib = sys.modules[module_name]
                version = getattr(lib, '__version__', 'Unknown')
            except:
                version = 'Unknown'
            
            print(f"[OK] {module_name:<15} (v{version})")
            installed.append(module_name)
        except ImportError:
            print(f"[X]  {module_name:<15} NOT FOUND!")
            missing.append(package_name)

    print("-" * 60)
    
    if missing:
        print(f"检测到 {len(missing)} 个缺失的依赖库。")
        print("请复制以下命令并在终端运行以修复环境：")
        print("\n" + "="*60)
        
        # 针对国内网络环境，我加上了清华源镜像加速
        install_cmd = f"pip install {' '.join(missing)} -i https://pypi.tuna.tsinghua.edu.cn/simple"
        print(install_cmd)
        
        print("="*60 + "\n")
    else:
        print("完美！所有依赖库已就绪。")
        print("系统状态：READY TO LAUNCH")

    # 额外检查：TTS 引擎在 Windows 下通常需要 comtypes
    if sys.platform == 'win32' and 'pyttsx3' in installed:
        try:
            import comtypes
        except ImportError:
            print("\n[注意] 检测到你在使用 Windows。")
            print("pyttsx3 通常需要 'comtypes' 才能驱动 Windows SAPI5 语音。")
            print("建议运行: pip install comtypes")

if __name__ == "__main__":
    check_dependencies()