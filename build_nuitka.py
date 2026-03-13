# -*- coding: utf-8 -*-
"""
AI小说生成器 - Nuitka打包构建脚本

================================================================================
模块功能概述
================================================================================
本模块提供使用Nuitka将AI小说生成器打包为独立可执行文件的自动化脚本。
Nuitka将Python代码编译为C/C++后再编译为机器码，相比PyInstaller具有更好的
运行性能和更小的打包体积。

================================================================================
核心功能
================================================================================
1. 从core/version.py读取版本信息
2. 动态生成Windows版本信息文件（version_info.txt）
3. 清理之前的构建输出（build/和dist/目录）
4. 配置Nuitka打包参数
5. 执行打包过程
6. 输出构建结果提示

================================================================================
Nuitka参数说明
================================================================================
- --standalone: 独立部署模式，生成包含所有依赖的文件夹
- --onefile: 单文件模式（可选，默认使用standalone）
- --windows-disable-console: 禁用控制台窗口
- --windows-icon-from-ico: 设置应用程序图标
- --windows-product-version: 设置产品版本
- --windows-file-version: 设置文件版本
- --windows-company-name: 设置公司名称
- --windows-product-name: 设置产品名称
- --windows-file-description: 设置文件描述
- --include-data-dir: 包含数据目录
- --include-module: 显式包含模块
- --nofollow-import-to: 不跟随导入指定模块（减小体积）
- --enable-plugin: 启用特定框架插件
- --output-dir: 输出目录
- --output-filename: 输出文件名

================================================================================
设计决策
================================================================================
- 采用standalone模式而非onefile，启动速度更快，便于调试
- 禁用控制台窗口，提供更专业的用户体验
- 显式包含动态加载的模块确保正确打包
- 排除不必要的模块以减小打包体积
- 启用PyQt5插件确保Qt相关依赖正确处理
- 动态生成版本信息，确保exe属性与代码版本同步

================================================================================
依赖要求
================================================================================
- Nuitka: Python编译打包工具
- 项目所有依赖模块需已安装
- C编译器: 需要安装MinGW或MSVC

使用方法:
    python.exe build_nuitka.py

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import shutil
import subprocess
import sys


def get_version_info():
    """
    从core/version.py模块读取版本信息。

    参数:
        无

    返回值:
        dict: 包含版本信息的字典，键包括：
            - version: 版本号字符串
            - product_name_en: 产品英文名称
            - product_name_cn: 产品中文名称
            - legal_copyright: 版权声明
            - author: 作者信息
            - github_url: GitHub仓库地址
            - license_url: 许可证链接

    异常:
        ImportError: 当无法导入version模块时

    使用示例:
        >>> info = get_version_info()
        >>> print(info['version'])
        '1.0.0'
    """
    from core.version import (
        __version__,
        PRODUCT_NAME_EN,
        PRODUCT_NAME_CN,
        LEGAL_COPYRIGHT,
        AUTHOR,
        GITHUB_REPO_URL,
        LICENSE_URL,
    )

    return {
        "version": __version__,
        "product_name_en": PRODUCT_NAME_EN,
        "product_name_cn": PRODUCT_NAME_CN,
        "legal_copyright": LEGAL_COPYRIGHT,
        "author": AUTHOR,
        "github_url": GITHUB_REPO_URL,
        "license_url": LICENSE_URL,
    }


def check_nuitka():
    """
    检查Nuitka是否已安装。

    参数:
        无

    返回值:
        bool: 如果Nuitka已安装返回True，否则返回False

    异常:
        无

    使用示例:
        >>> if check_nuitka():
        ...     print("Nuitka is installed")
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"检测到 Nuitka 版本: {result.stdout.strip()}")
            return True
    except Exception:
        pass
    return False


def install_nuitka():
    """
    自动安装Nuitka。

    参数:
        无

    返回值:
        bool: 安装成功返回True，否则返回False

    异常:
        无

    使用示例:
        >>> if install_nuitka():
        ...     print("Nuitka installed successfully")
    """
    print("正在安装 Nuitka...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "nuitka",
                "ordered-set",
                "zstandard",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("Nuitka 安装成功!")
            return True
        else:
            print(f"安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"安装过程出错: {e}")
        return False


def clean_build_dirs(clean_cache=False):
    """
    清理构建输出目录。

    清理以下目录：
    - build/
    - dist/
    - *.dist/ (Nuitka生成的分发目录)
    - *.onefile-build/ (Nuitka单文件构建目录)

    如果 clean_cache=True，还会清理：
    - *.build/ (Nuitka生成的构建目录，包含编译缓存)

    参数:
        clean_cache (bool): 是否清理编译缓存目录，默认False以加速后续构建

    返回值:
        无

    异常:
        PermissionError: 无法删除目录时

    使用示例:
        >>> clean_build_dirs()  # 保留缓存
        >>> clean_build_dirs(clean_cache=True)  # 清理所有包括缓存
    """
    dirs_to_clean = ["dist"]

    if clean_cache:
        dirs_to_clean.insert(0, "build")

    for item in os.listdir("."):
        if os.path.isdir(item):
            if item.endswith(".dist") or item.endswith(".onefile-build"):
                dirs_to_clean.append(item)
            elif clean_cache and item.endswith(".build"):
                dirs_to_clean.append(item)

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            try:
                shutil.rmtree(dir_name)
            except PermissionError as e:
                print(f"警告: 无法删除 {dir_name}: {e}")


def build(clean_cache=False):
    """
    执行应用程序打包构建流程。

    该函数完成以下操作：
    1. 检查并安装Nuitka
    2. 从version.py读取版本信息
    3. 清理之前的构建输出目录
    4. 配置Nuitka打包参数
    5. 执行打包命令
    6. 输出构建完成提示

    参数:
        clean_cache (bool): 是否清理编译缓存，默认False以加速后续构建

    返回值:
        无

    异常:
        可能抛出以下异常：
        - PermissionError: 无法删除旧的构建目录时
        - subprocess.CalledProcessError: 打包过程中出错时

    使用示例:
        >>> build()  # 使用缓存加速
        >>> build(clean_cache=True)  # 完全重新构建

    输出位置:
        打包完成后，可执行文件位于 dist/{PRODUCT_NAME_CN}/{PRODUCT_NAME_CN}.exe
    """
    if not check_nuitka():
        if not install_nuitka():
            print("错误: 无法安装Nuitka，请手动安装后重试")
            print("安装命令: pip install nuitka ordered-set zstandard")
            return

    version_info = get_version_info()
    version = version_info["version"]
    exe_name = version_info["product_name_cn"]
    author = version_info["author"]
    copyright_info = version_info["legal_copyright"]

    version_parts = version.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    major, minor, patch, build_num = version_parts[:4]
    version_tuple = f"{major}.{minor}.{patch}.{build_num}"

    print("=" * 60)
    print("Nuitka 打包配置")
    print("=" * 60)
    print(f"版本: {version}")
    print(f"产品名称: {exe_name}")
    print(f"作者: {author}")
    print(f"版权: {copyright_info}")
    print("=" * 60)
    print()

    clean_build_dirs(clean_cache)

    os.makedirs("dist", exist_ok=True)

    nuitka_args = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--windows-disable-console",
        f"--windows-icon-from-ico=icon.ico",
        f"--windows-product-version={version_tuple}",
        f"--windows-file-version={version_tuple}",
        f"--windows-company-name={author}",
        f"--windows-product-name={exe_name}",
        f"--windows-file-description={exe_name}",
        "--enable-plugin=pyqt5",
        "--include-data-dir=ui_qt=ui_qt",
        "--include-module=qasync",
        "--include-module=jaraco",
        "--include-module=jaraco.functools",
        "--include-module=jaraco.context",
        "--include-module=jaraco.text",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",
        "--nofollow-import-to=notebook",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tests",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=wheel",
        "--nofollow-import-to=pip",
        "--nofollow-import-to=black",
        "--nofollow-import-to=flake8",
        "--nofollow-import-to=isort",
        "--nofollow-import-to=mypy",
        "--nofollow-import-to=pylint",
        "--nofollow-import-to=cython",
        "--nofollow-import-to=docutils",
        "--nofollow-import-to=sphinx",
        "--nofollow-import-to=torch",
        "--nofollow-import-to=transformers",
        "--nofollow-import-to=sentence_transformers",
        "--nofollow-import-to=onnxruntime",
        "--nofollow-import-to=keybert",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=sklearn",
        "--nofollow-import-to=customtkinter",
        "--nofollow-import-to=darkdetect",
        "--output-dir=dist",
        f"--output-filename={exe_name}.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "main.py",
    ]

    print("开始 Nuitka 编译打包...")
    print("这可能需要较长时间，请耐心等待...")
    print()

    try:
        result = subprocess.run(nuitka_args, check=True)
        print("\n" + "=" * 60)
        print("Build complete!")
        print("=" * 60)
        print(f"输出位置: dist/{exe_name}.dist/")
        print(f"可执行文件: dist/{exe_name}.dist/{exe_name}.exe")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n打包过程出错: {e}")
        print("请检查错误信息并重试")
    except KeyboardInterrupt:
        print("\n用户取消打包")


def build_onefile(clean_cache=False):
    """
    执行单文件模式打包构建流程。

    与build()类似，但生成单个可执行文件而非文件夹。
    单文件模式便于分发，但启动速度较慢。

    参数:
        clean_cache (bool): 是否清理编译缓存，默认False以加速后续构建

    返回值:
        无

    异常:
        可能抛出以下异常：
        - PermissionError: 无法删除旧的构建目录时
        - subprocess.CalledProcessError: 打包过程中出错时

    使用示例:
        >>> build_onefile()  # 使用缓存加速
        >>> build_onefile(clean_cache=True)  # 完全重新构建

    输出位置:
        打包完成后，可执行文件位于 dist/{PRODUCT_NAME_CN}.exe
    """
    if not check_nuitka():
        if not install_nuitka():
            print("错误: 无法安装Nuitka，请手动安装后重试")
            print("安装命令: pip install nuitka ordered-set zstandard")
            return

    version_info = get_version_info()
    version = version_info["version"]
    exe_name = version_info["product_name_cn"]
    author = version_info["author"]
    copyright_info = version_info["legal_copyright"]

    version_parts = version.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    major, minor, patch, build_num = version_parts[:4]
    version_tuple = f"{major}.{minor}.{patch}.{build_num}"

    print("=" * 60)
    print("Nuitka 单文件打包配置")
    print("=" * 60)
    print(f"版本: {version}")
    print(f"产品名称: {exe_name}")
    print(f"作者: {author}")
    print(f"版权: {copyright_info}")
    print("=" * 60)
    print()

    clean_build_dirs(clean_cache)

    os.makedirs("dist", exist_ok=True)

    nuitka_args = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--windows-disable-console",
        f"--windows-icon-from-ico=icon.ico",
        f"--windows-product-version={version_tuple}",
        f"--windows-file-version={version_tuple}",
        f"--windows-company-name={author}",
        f"--windows-product-name={exe_name}",
        f"--windows-file-description={exe_name}",
        "--enable-plugin=pyqt5",
        "--include-data-dir=ui_qt=ui_qt",
        "--include-module=qasync",
        "--include-module=jaraco",
        "--include-module=jaraco.functools",
        "--include-module=jaraco.context",
        "--include-module=jaraco.text",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",
        "--nofollow-import-to=notebook",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tests",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=wheel",
        "--nofollow-import-to=pip",
        "--nofollow-import-to=black",
        "--nofollow-import-to=flake8",
        "--nofollow-import-to=isort",
        "--nofollow-import-to=mypy",
        "--nofollow-import-to=pylint",
        "--nofollow-import-to=cython",
        "--nofollow-import-to=docutils",
        "--nofollow-import-to=sphinx",
        "--nofollow-import-to=torch",
        "--nofollow-import-to=transformers",
        "--nofollow-import-to=sentence_transformers",
        "--nofollow-import-to=onnxruntime",
        "--nofollow-import-to=keybert",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=sklearn",
        "--nofollow-import-to=customtkinter",
        "--nofollow-import-to=darkdetect",
        "--output-dir=dist",
        f"--output-filename={exe_name}.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "main.py",
    ]

    print("开始 Nuitka 单文件编译打包...")
    print("这可能需要较长时间，请耐心等待...")
    print()

    try:
        result = subprocess.run(nuitka_args, check=True)
        print("\n" + "=" * 60)
        print("Build complete!")
        print("=" * 60)
        print(f"输出位置: dist/")
        print(f"可执行文件: dist/{exe_name}.exe")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n打包过程出错: {e}")
        print("请检查错误信息并重试")
    except KeyboardInterrupt:
        print("\n用户取消打包")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI小说生成器 Nuitka 打包脚本")
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="使用单文件模式打包（默认使用standalone模式）",
    )
    parser.add_argument(
        "--clean-cache",
        action="store_true",
        help="清理编译缓存，完全重新构建",
    )

    args = parser.parse_args()

    if args.onefile:
        build_onefile(clean_cache=args.clean_cache)
    else:
        build(clean_cache=args.clean_cache)
