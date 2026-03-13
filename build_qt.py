# -*- coding: utf-8 -*-
"""
AI小说生成器 - PyInstaller打包构建脚本

================================================================================
模块功能概述
================================================================================
本模块提供使用PyInstaller将AI小说生成器打包为独立可执行文件的自动化脚本。
打包后的程序可在没有Python环境的Windows系统上独立运行。

================================================================================
核心功能
================================================================================
1. 从core/version.py读取版本信息
2. 动态生成Windows版本信息文件（version_info.txt）
3. 清理之前的构建输出（build/和dist/目录）
4. 配置PyInstaller打包参数
5. 执行打包过程
6. 输出构建结果提示

================================================================================
打包配置说明
================================================================================
- --name: 指定输出可执行文件名称（使用PRODUCT_NAME_CN）
- --windowed: 无控制台窗口模式，适合GUI应用程序
- --onedir: 目录模式，所有依赖打包到一个文件夹中（启动更快，便于调试）
- --icon: 设置应用程序图标
- --version-file: 设置exe版本信息（包含版本号、版权、作者等）
- --add-data: 添加UI模块数据文件
- --hidden-import: 显式指定隐式导入的模块
- --exclude-module: 排除不需要的模块以减小体积
- --noupx: 禁用UPX压缩（避免兼容性问题）
- --strip: 去除符号信息减小体积
- --optimize: 优化字节码等级
- --noconfirm: 覆盖输出目录时不提示确认

================================================================================
设计决策
================================================================================
- 采用目录模式（onedir）而非单文件模式，启动速度更快，便于调试
- 使用--windowed模式隐藏控制台，提供更专业的用户体验
- 显式添加隐式导入确保动态加载的模块被正确打包
- 排除不必要的科学计算子模块，大幅减小打包体积
- 禁用UPX压缩避免某些系统上的兼容性问题
- 动态生成版本信息文件，确保exe属性与代码版本同步

================================================================================
依赖要求
================================================================================
- PyInstaller: Python打包工具
- 项目所有依赖模块需已安装

使用方法:
    python.exe build_qt.py

作者: ItsTimeTooSleep
创建日期: 2026年 03月
"""

import os
import shutil

import PyInstaller.__main__


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


def generate_version_file(version_info):
    """
    生成Windows版本信息文件内容。

    该函数根据提供的版本信息生成符合Windows PE文件格式的版本信息文件。
    生成的文件将被PyInstaller用于设置exe文件的属性。

    参数:
        version_info (dict): 包含版本信息的字典，由get_version_info()返回

    返回值:
        str: 版本信息文件的完整内容字符串

    使用示例:
        >>> info = get_version_info()
        >>> content = generate_version_file(info)
        >>> with open('version_info.txt', 'w', encoding='utf-8') as f:
        ...     f.write(content)

    设计说明:
        - VS_FIXEDFILEINFO结构定义文件版本和产品版本
        - StringFileInfo包含可显示的版本信息
        - VarFileInfo指定语言和字符集
        - 使用UTF-8编码支持中文产品名称
    """
    version = version_info["version"]
    version_parts = version.split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    major, minor, patch, build = version_parts[:4]

    version_tuple = f"{major}, {minor}, {patch}, {build}"

    content = f"""# UTF-8
#
# AI小说生成器 - Windows版本信息文件
# 由build_qt.py自动生成，请勿手动修改
#

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'080404b0',
          [
            StringStruct(u'CompanyName', u'{version_info["author"]}'),
            StringStruct(u'FileDescription', u'{version_info["product_name_cn"]}'),
            StringStruct(u'FileVersion', u'{version}'),
            StringStruct(u'InternalName', u'{version_info["product_name_en"]}'),
            StringStruct(u'LegalCopyright', u'{version_info["legal_copyright"]}'),
            StringStruct(u'LegalTrademarks', u'AGPL-3.0'),
            StringStruct(u'OriginalFilename', u'{version_info["product_name_cn"]}.exe'),
            StringStruct(u'ProductName', u'{version_info["product_name_cn"]}'),
            StringStruct(u'ProductVersion', u'{version}'),
            StringStruct(u'Comments', u'项目主页: {version_info["github_url"]}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"""
    return content


def build():
    """
    执行应用程序打包构建流程。

    该函数完成以下操作：
    1. 从version.py读取版本信息
    2. 生成版本信息文件（version_info.txt）
    3. 清理之前的构建输出目录（build/和dist/）
    4. 配置PyInstaller打包参数（包含优化选项）
    5. 执行打包命令
    6. 清理临时版本信息文件
    7. 输出构建完成提示

    参数:
        无

    返回值:
        无

    异常:
        可能抛出以下异常：
        - PermissionError: 无法删除旧的构建目录时
        - PyInstaller.exceptions: 打包过程中出错时

    使用示例:
        >>> build()
        Build complete. Check dist/ folder.

    设计说明:
        - 每次构建前清理旧文件，避免缓存问题
        - 目录模式（onedir）启动更快，便于调试
        - 隐式导入确保动态加载模块（如qasync）正确打包
        - 排除不必要模块减小打包体积
        - 禁用UPX避免Windows Defender误报和兼容性问题
        - 版本信息文件在打包后自动清理

    输出位置:
        打包完成后，可执行文件位于 dist/{PRODUCT_NAME_CN}/{PRODUCT_NAME_CN}.exe
    """
    version_info = get_version_info()
    version_file_content = generate_version_file(version_info)
    version_file_path = "version_info.txt"

    with open(version_file_path, "w", encoding="utf-8") as f:
        f.write(version_file_content)

    print(f"版本信息: {version_info['version']}")
    print(f"产品名称: {version_info['product_name_cn']}")
    print(f"作者: {version_info['author']}")
    print(f"版权: {version_info['legal_copyright']}")
    print()

    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    exe_name = version_info["product_name_cn"]

    args = [
        "main.py",
        f"--name={exe_name}",
        "--windowed",
        "--onedir",
        "--icon=icon.ico",
        f"--version-file={version_file_path}",
        "--add-data=ui_qt;ui_qt",
        "--noconfirm",
        "--clean",
        "--hidden-import=qasync",
        "--hidden-import=jaraco",
        "--hidden-import=jaraco.functools",
        "--hidden-import=jaraco.context",
        "--hidden-import=jaraco.text",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        "--exclude-module=test",
        "--exclude-module=tests",
        "--exclude-module=unittest",
        "--exclude-module=pytest",
        "--exclude-module=wheel",
        "--exclude-module=pip",
        "--exclude-module=black",
        "--exclude-module=flake8",
        "--exclude-module=isort",
        "--exclude-module=mypy",
        "--exclude-module=pylint",
        "--exclude-module=cython",
        "--exclude-module=docutils",
        "--exclude-module=sphinx",
    ]

    PyInstaller.__main__.run(args)

    if os.path.exists(version_file_path):
        os.remove(version_file_path)

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"输出位置: dist/{exe_name}/")
    print(f"可执行文件: dist/{exe_name}/{exe_name}.exe")
    print("=" * 60)


if __name__ == "__main__":
    build()
