"""Add/update the non-driving specification records in the active HT2806 document."""
import FreeCAD as A

ROWS = [
    ('额定电压',12,'V',''),
    ('额定电流',0.81,'A',''),
    ('额定扭矩',0.06,'N·m',''),
    ('额定转速',950,'rpm',''),
    ('最大转速',2335,'rpm','原表英文 Peak Speed'),
    ('堵转扭矩',0.09,'N·m','原表英文 Peak torque'),
    ('堵转电流',1.22,'A','原表英文 Peak current'),
    ('相间电阻',5.13,'Ω',''),
    ('相间电感',1.64,'mH',''),
    ('转速常数',195,'rpm/V',''),
    ('扭矩常数',0.07,'N·m/A',''),
    ('转子惯量',36,'g·cm²','原表单位 gcm^2'),
    ('极对数',7,'1','原表 Pairs'),
    ('不带编码器重量',45.4,'g',''),
    ('带编码器重量',55.4,'g',''),
    ('不带编码器直径',34.6,'mm','原表 Ø34.6×18.3，拆分记录'),
    ('不带编码器总长',18.3,'mm','与现有尺寸图推算总长18相差0.3；未用于修改几何'),
    ('带编码器直径',34.6,'mm','原表 Ø34.6×24.7，拆分记录'),
    ('带编码器总长',24.7,'mm','编码器未建模'),
    ('工作温度下限',-10,'°C','原表 -10～80，拆分记录'),
    ('工作温度上限',80,'°C',''),
    ('最高退磁温度',120,'°C','按原表名称抄录'),
]

def update(d):
    p=d.getObject('Performance') or d.addObject('Spreadsheet::Sheet','Performance')
    p.Label='性能记录'
    for c,t in zip('ABCD',('参数','数值','单位','说明')):p.set(c+'1',t)
    for i,(label,value,unit,note) in enumerate(ROWS,2):
        for c,v in zip('ABCD',(label,str(value),unit,note)):p.set(c+str(i),v)
    i=len(ROWS)+2
    for label,note in [
        ('编码器型号','AS5048A/AS5600/AS5047P；原表列出的型号，不推定本件实际选型'),
        ('表格性质','性能记录表，不驱动几何；数值按用户规格截图抄录，非实测数据'),
        ('参考来源','用户提供 tb_image_share_1793500707389.png；保存于 references/性能参数.png'),
        ('尺寸差异','安装图机身15+凸台3=18；规格表不带编码器18.3，测量基准或版本差异待确认')]:
        p.set('A'+str(i),label);p.set('B'+str(i),'');p.set('C'+str(i),'1');p.set('D'+str(i),note);i+=1
    for c,w in [('A',190),('B',95),('C',90),('D',650)]:p.setColumnWidth(c,w)
    p.setStyle('A1:D1','bold')
    d.recompute()
    return p

if __name__=='__main__':
    d=A.ActiveDocument
    assert d and d.getObject('Motor') and d.Label=='HT2806'
    before=d.Motor.Shape.Volume
    update(d)
    assert abs(before-d.Motor.Shape.Volume)<1e-9
    d.save()
    print('HT2806 specifications saved:',len(ROWS),'numeric rows; geometry unchanged')
