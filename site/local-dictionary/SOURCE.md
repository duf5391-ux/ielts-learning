# 本地英汉词典

数据：[ECDICT](https://github.com/skywind3000/ECDICT)，MIT 许可证，下载与构建于 2026-09-19。固定版本、原始文件地址与 SHA-256 见 [provenance.json](provenance.json)。

保留通用英汉释义、已有英文释义、音标、词性与词形数据。浏览器按需读取本机分片，查词无需在线接口。未收录的词不会自动联网。音标字段并非每条都有；词库未包含统一的真人发音录音。原有课程搭配、例句与词典通用义项分别显示。

已构建词条：770,611。词形对应依据词库 exchange 字段。

维护源位于工作区 local-dictionary；安装脚本为 integrate_local_dictionary.py。原始 CSV 保存在工作区 source 中，不需要放进浏览器存储。
