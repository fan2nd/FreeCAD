# FreeCAD 工程集合

每个工程放在 `projects/<工程名>/`。每个工程内部按用途统一分目录；屏幕支架的 V1、V2 各自使用相同结构。

```text
projects/<工程名>/（屏幕支架下再分 v1/、v2/）
├── models/     FreeCAD 工程和 STEP 模型
├── scripts/    构建及预览生成脚本
├── previews/   PNG、SVG 预览
└── print/      STL、3MF 打印文件
```

仅创建实际有文件的目录。构建生成的 `reports/` 不提交；旧说明、校验脚本和草案集中保留在根目录 `.local/`，不进入 Git。

## 屏幕支架

| 版本 | 位置 | 说明 |
| --- | --- |
| `projects/slotted-plate/` | 推力计与笔槽板；参数化装配、打印文件及尺寸标注页面，部分尺寸待确认 | --- |
| V1 | [projects/screen-stand/v1](projects/screen-stand/v1/) | 主板水平放置，屏幕中间四孔固定 |
| V2 | [projects/screen-stand/v2](projects/screen-stand/v2/) | 主板背装、一体短底座、屏幕侧朝下打印 |

两个版本均包含 FreeCAD 模型、STEP、STL、生成脚本和预览。早期草案保留在 `.local/`。

## 其他工程

| 目录 | 内容 |
| --- | --- |
| `projects/power-myh4621/` | 电源底座与支架 |
| `projects/h7s78-dk/` | H7S78 底座、盖板及圆角重建工程 |
| `projects/nucleo/` | Nucleo 底座 |
| `projects/xilinx-ft232/` | Xilinx FT232 支架 |
| `projects/zjy096t-display/` | 中景园显示屏模型 |
| `projects/pc300/` | PC300 模型 |
| `projects/qfp-trays/` | QFP 托盘 |
| `projects/massage-shower/` | 按摩花洒、重建脚本和导出文件 |
| `projects/solder-fume-extractor/` | 焊锡吸烟器、配件及建模脚本 |
| `projects/programming-clip/` | 烧录夹 |
| `projects/medicine-box/` | 药仓 |

## 文件管理约定

- 提交工程、构建脚本、预览和打印文件，以及本说明和 `.gitignore`。
- `models/` 中有意保留的原始模型（如 `h7s78-dk-original.FCStd`）是重建输入，不是自动备份。
- 脚本根据自身位置定位工程目录，输出到对应分类目录，不再使用 `output/`。
- 自动备份、缓存、临时文件、`reports/` 和 `.local/` 由 [.gitignore](.gitignore) 排除。
- 本次仅整理路径和脚本，不改变 CAD 几何；FreeCAD 最近文件列表可能需要重新选择新位置。
