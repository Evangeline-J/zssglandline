// index.js

const fs = require('fs');
const VPTreeFactory = require('../draw/js/third_party/vptree.js');

// 1. 准备 polylines 数据（每一项是一条单行数组）
const polylines = [
    [3,-250,1,-245,0,-241,-3,-235,-6,-228,-9,-224,-15,-216,-20,-210,-25,-204,-29,-197,-32,-193,-37,-186,-44,-176,-48,-171,-56,-161,-61,-156,-69,-149,-73,-145,-78,-140,-86,-133,-92,-127,-97,-122,-104,-115,-110,-109,-114,-102,-120,-92,-130,-77,-136,-67,-143,-55,-149,-44,-158,-32,-164,-24,-169,-15,-173,-5,-177,5,-182,17,-186,28,-188,34,-190,46,-193,61,-194,71,-194,82,-190,98,-187,110,-177,129,-168,143,-159,155,-147,167,-136,177,-124,186,-108,197,-96,205,-83,211,-63,222,-52,227,-39,233,-27,238,-21,241,-12,247,-3,250]
]
// 2. 基于余弦相似度的距离函数
function cosDistance(vector1, vector2) {
    // 检查向量长度一致且为偶数（每个点包含x,y坐标）
    if (vector1.length !== vector2.length || vector1.length % 2 !== 0) {
        throw new Error('向量格式不正确：必须为偶数长度且长度一致');
    }

    let a = 0, b = 0;
    const length = vector1.length;
    
    // 计算点积和叉积的累积量
    for (let i = 0; i < length; i += 2) {
        const x1 = vector1[i];
        const y1 = vector1[i + 1];
        const x2 = vector2[i];
        const y2 = vector2[i + 1];
        
        a += x1 * x2 + y1 * y2;  // 点积
        b += x1 * y2 - y1 * x2;  // 叉积的z分量
    }

    // 处理除以零的情况
    if (a === 0) {
        return Math.PI / 2;  // 90度夹角
    }

    // 计算整体旋转角度
    const angle = Math.atan(b / a);
    
    // 计算余弦相似度距离
    const magnitude = Math.sqrt(a*a + b*b);
    const cosine = a / magnitude;
    return Math.acos(cosine);  // 返回弧度值（0~π）
}

// 3. 构建 VP-Tree（使用新距离函数）
const vpTree = VPTreeFactory.build(polylines, cosDistance, 10);

// 4. 序列化并写入文件（其余代码保持不变）
const vpTreeStr = vpTree.stringify();
const polylineLines = polylines
  .map(arr => '    ' + JSON.stringify(arr))
  .join(',\n');

const finalJson =
`{
  "polylines": [
${polylineLines}
  ],
  "vpTree": ${JSON.stringify(vpTreeStr)}
}`;

fs.writeFileSync('polylines_and_vptree.json', finalJson, 'utf8');
console.log('已生成 polylines_and_vptree.json');