"""Short display names; internal IDs remain stable for feature references."""
import re

def apply(doc):
    doc.Label='管路压力工装'
    direct={'Lower':'下座','Upper':'上盖',
            'TubeReference':'管道参考','GridReference':'敏感栅参考','GaugeReference':'应变片参考','Parameters':'参数记录','DesignNotes':'说明'}
    stems={'BaseBlank':'底板','BaseTubeTool':'下管槽刀具','BaseGroove':'下管槽',
           'WallReliefTool':'限位避让刀具','WallRelief':'限位避让','TipBridge':'端部薄梁','SideWall':'侧壁','BaseWalls':'侧壁合并','Post':'螺丝柱','Pilot':'底孔刀具',
           'BasePosts':'螺丝柱合并','PilotCut':'底孔切除','CoverBlank':'盖板',
           'CoverTubeTool':'上管槽刀具','CoverGroove':'上管槽','WindowTool':'窗口刀具',
           'CoverWindow':'窗口','Flexure':'薄梁','RootRamp':'根部圆角','TipRamp':'端部圆角',
           'RootStiff':'焊点支撑','RootRelief':'后圆角','StiffRamp':'前圆角','StiffSegment':'加厚段','ShoulderSketch':'收窄草图','ShoulderTool':'收窄刀具','ShoulderTrim':'收窄','ContactPad':'触头端块','ContactBlank':'触头毛坯','SaddleTool':'鞍面刀具',
           'SaddleContact':'鞍面','CoverFlexure':'悬臂合并','PostRelief':'柱避让刀具',
           'ReliefCut':'柱避让','ScrewClearance':'通孔刀具','ClearanceCut':'通孔切除'}
    for o in doc.Objects:
        if o.Name in direct:o.Label=direct[o.Name];continue
        name=o.Name;suffix=''
        for token,label in [('Sketch','草图'),('Start','起截面'),('End','末截面')]:
            if name.endswith(token):name=name[:-len(token)];suffix=label;break
        m=re.fullmatch(r'(.*?)(\d*)',name);stem,num=m.groups()
        if stem in stems:o.Label=stems[stem]+(str(int(num)+1) if num else '')+suffix
